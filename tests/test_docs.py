"""文档本身的"体检"。

起因：`projects/demo/decisions.md` 里 v7 条目被追加了两遍，`tests/test_render.py`
也曾整块重复。这类错误不影响代码运行，pytest 也照样全绿 —— 所以给文档也加一层校验。
"""

import glob
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 需要长期维护的文档：重复、路径、链接都要查
DOC_GLOBS = (
    "README.md",
    "agents.md",
    "USER.md",
    ".workbuddy/skills/*/SKILL.md",
    "projects/*/decisions.md",
    "projects/*/brief.md",
    "docs/music_knowledge/*.md",
)

# 冻结的历史记录（code review / 审核报告）：只查整块重复。
# 不查路径 —— 它们会**故意引用当时不存在的路径**（如 tools/synthesize.sh），
# 那是记录的一部分，改成"正确"反而失真。
ARCHIVE_GLOBS = ("docs/*.md",)

# 窗口大小：8 行足够长，短表头/空行的自然重复不会被误判
WINDOW = 8
MIN_WINDOW_CHARS = 80


def _docs(include_archive=True):
    patterns = DOC_GLOBS + (ARCHIVE_GLOBS if include_archive else ())
    paths = []
    for pattern in patterns:
        paths.extend(sorted(glob.glob(os.path.join(ROOT, pattern))))
    return paths


def _lines(path):
    with open(path, encoding="utf-8") as f:
        return [line.rstrip() for line in f.read().splitlines()]


def _rel(path):
    return os.path.relpath(path, ROOT)


class TestNoDuplicateBlocks:
    def test_no_repeated_block(self):
        """同一份文档里不该出现两段完全相同的 8 行内容。

        heredoc 追加被执行两次时，产出的正是这种重复；光看 git diff 容易漏。
        """
        offenders = []
        for path in _docs(include_archive=True):
            lines = _lines(path)
            seen = {}
            for start in range(len(lines) - WINDOW + 1):
                window = tuple(lines[start:start + WINDOW])
                if sum(len(x.strip()) for x in window) < MIN_WINDOW_CHARS:
                    continue
                if window in seen:
                    offenders.append(
                        f"{_rel(path)} 第 {seen[window] + 1} 行与第 {start + 1} 行起"
                        f"的 {WINDOW} 行完全重复"
                    )
                    break
                seen[window] = start

        assert not offenders, "文档出现重复段落：\n  " + "\n  ".join(offenders)

    def test_covers_expected_files(self):
        """防止 glob 写错导致这条测试空跑（空跑等于没有）。"""
        rels = {_rel(p) for p in _docs()}
        assert "README.md" in rels
        assert "agents.md" in rels
        assert any("SKILL.md" in r for r in rels)
        assert any("decisions.md" in r for r in rels)


class TestDecisionsLog:
    def _logs(self):
        return sorted(glob.glob(os.path.join(ROOT, "projects", "*", "decisions.md")))

    def test_version_headings_unique_and_ordered(self):
        """`## v3 — …` 这种版本标题必须唯一、且编号递增。"""
        for path in self._logs():
            versions = []
            for line in _lines(path):
                matched = re.match(r"^## v(\d+)\s+[—–-]", line)
                if matched:
                    versions.append((int(matched.group(1)), line))

            numbers = [n for n, _ in versions]
            duplicated = [n for n in set(numbers) if numbers.count(n) > 1]
            assert not duplicated, f"{_rel(path)} 版本标题重复: v{duplicated}"

            assert numbers == sorted(numbers), \
                f"{_rel(path)} 版本标题顺序乱了: {numbers}"

    def test_has_at_least_one_entry(self):
        for path in self._logs():
            assert re.search(r"^## v\d+", "\n".join(_lines(path)), re.M), \
                f"{_rel(path)} 没有任何版本记录"


class TestSkillFrontmatter:
    def _skills(self):
        return sorted(glob.glob(os.path.join(ROOT, ".workbuddy", "skills", "*", "SKILL.md")))

    def test_name_matches_directory(self):
        """skill 的 name 必须等于目录名，否则调用时找不到。"""
        for path in self._skills():
            text = open(path, encoding="utf-8").read()
            head = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            assert head, f"{_rel(path)} 缺 frontmatter"

            name = re.search(r"^name:\s*(.+)$", head.group(1), re.M)
            assert name, f"{_rel(path)} frontmatter 缺 name"
            assert name.group(1).strip() == os.path.basename(os.path.dirname(path)), \
                f"{_rel(path)} 的 name 与目录名不一致"

    def test_description_present(self):
        """description 是触发词，写太短会匹配不上用户的说法。"""
        for path in self._skills():
            text = open(path, encoding="utf-8").read()
            head = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            desc = re.search(r"^description:\s*(.+)$", head.group(1), re.M)
            assert desc, f"{_rel(path)} 缺 description"
            assert len(desc.group(1)) >= 10, f"{_rel(path)} 的 description 太短"


class TestReferencedPaths:
    """文档里用反引号写出的仓库相对路径必须真实存在。

    只检查带 `/` 且不像占位符的 token（`projects/<dir>/config.json` 这类跳过）。
    `projects/<name>/` 下的文档允许写**相对项目目录**的路径，如 `music/output/x.mid`。
    """

    SUFFIXES = (".py", ".sh", ".md", ".json", ".mid", ".yml", ".toml")
    # demo-vN.mid 这类模板不算真实路径
    PLACEHOLDER = re.compile(r"\bv[A-Z]\b")

    def _tokens(self, path):
        text = open(path, encoding="utf-8").read()
        for token in re.findall(r"`([^`\n]+)`", text):
            token = token.strip()
            if "/" not in token or " " in token:
                continue
            if any(bad in token for bad in ("<", "*", "…", "~")):
                continue
            if self.PLACEHOLDER.search(token):
                continue
            if not token.endswith(self.SUFFIXES) and not token.endswith("/"):
                continue
            yield token

    def _candidates(self, doc_path, token):
        """先按仓库根解析，再按所属项目目录解析。"""
        yield os.path.join(ROOT, token)
        parts = _rel(doc_path).split(os.sep)
        if len(parts) >= 3 and parts[0] == "projects":
            yield os.path.join(ROOT, "projects", parts[1], token)

    def test_paths_exist(self):
        missing = []
        for path in _docs(include_archive=False):
            for token in self._tokens(path):
                if not any(os.path.exists(c) for c in self._candidates(path, token)):
                    missing.append(f"{_rel(path)} → {token}")
        assert not missing, "文档引用了不存在的路径：\n  " + "\n  ".join(missing)



class TestReadmeSync:
    """README 里的关键事实必须和代码一致，否则比"没写"更糟。"""

    def test_track_count_matches_code(self):
        from core.arrange import TRACK_KEYS
        from core.compose import TRACKS

        assert set(TRACKS) == set(TRACK_KEYS)

        readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
        assert f"{len(TRACK_KEYS)} 条" in readme or f"{len(TRACK_KEYS)} 轨" in readme, \
            f"README 里没写对轨数（代码是 {len(TRACK_KEYS)} 条）"

        for key in TRACK_KEYS:
            assert f"`{key}`" in readme, f"README 的轨表没提 {key}"


class TestMarkdownLinks:
    """相对链接必须指向真实文件。

    知识库靠索引页串起来，链接一断，使用者就找不到东西；
    这种错在编辑器里点一下才能发现，所以交给测试。
    """

    LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    SKIP_PREFIX = ("http://", "https://", "mailto:", "#")

    def test_relative_links_resolve(self):
        broken = []
        for path in _docs(include_archive=True):
            base = os.path.dirname(path)
            text = open(path, encoding="utf-8").read()
            for target in self.LINK.findall(text):
                target = target.strip()
                if target.startswith(self.SKIP_PREFIX):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                if not os.path.exists(os.path.join(base, target)):
                    broken.append(f"{_rel(path)} → {target}")
        assert not broken, "文档里的相对链接失效：\n  " + "\n  ".join(broken)
