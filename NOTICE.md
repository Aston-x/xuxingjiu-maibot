# 第三方组件与参考实现

本项目（许杏玖 / Xuxingjiu）以 GPL-3.0 许可发布，见 [`LICENSE`](LICENSE)。
仓库内**不包含**下列第三方组件的源码或二进制，仅在文档中说明如何获取与对接。
各组件版权归其各自作者所有。

## 运行时依赖（使用者自行安装）

| 组件 | 许可 | 用途 | 获取方式 |
| --- | --- | --- | --- |
| [MaiBot](https://github.com/Mai-with-u/MaiBot) | GPL-3.0 | 大脑、插件运行时与平台 IO | 自行从上游 clone；本仓库只提供补丁与配置模板 |
| SnowLuma | 专有 / 见上游 | QQ 协议端，只提供 OneBot v11 接口 | 项目已转私有、停止更新；本仓库不附带任何二进制 |
| [OneBot v11](https://github.com/botuniverse/onebot-11) | 见上游 | 机器人应用层通信标准 | 协议规范 |
| [MaiBot-Telegram-Adapter](https://github.com/exynos967/MaiBot-Telegram-Adapter) | AGPL-3.0-or-later | 兼容旧版 MaiBot 的 Telegram Bot API 适配器 | 外部插件，本仓库不复制其源码 |
| [MaiBot Telegram 官方适配器](https://github.com/Mai-with-u/Maibot-telegram-adaptor) | MIT | 新版 MaiBot 的 Telegram 适配器 | 外部插件，达到宿主版本要求后再评估 |
| [memfade](https://github.com/Aston-x/memfade) | MIT | 会话作用域长期记忆与淡化引擎 | 独立仓库 |

## Python / Node 依赖

本仓库只包含配置模板、补丁与脚本，不随仓库分发第三方依赖、插件源码或运行时数据。
各组件许可信息见其自身仓库。

## 免责声明

本项目仅供**学习与研究**用途：

- 仓库内不提供账号、Cookie、Bot Token、密钥或代理服务；
- QQ 平台与 Telegram 平台的使用均须遵守对应服务条款；
- 使用者需自行承担账号、内容与合规责任；
- 由此产生的一切后果由使用者自行承担，项目作者不承担任何责任。
