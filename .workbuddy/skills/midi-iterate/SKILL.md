---
name: midi-iterate
description: 根据 Logic 预览反馈，只改代码重新生成 MIDI，不手动改二进制
---

# midi-iterate

## 触发
用户回传 preview 问题：“鼓太弱/贝斯过密/副歌没记忆点”。

## 流程
1. 读项目 decisions.md 和上一版 patterns
2. 只改对应层：config / theory / patterns
3. 版本号 +1，重新跑 compose
4. 输出 diff 说明：改了哪行逻辑、听感预期变化

## 纪律
- 不改用户已在 Logic 里手调的自动化
- 每次只迭代 1~2 个音乐问题