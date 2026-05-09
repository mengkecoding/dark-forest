# 🌌 黑暗森林社会模拟器

基于《三体》黑暗森林理论的多文明博弈模拟器。12 个文明在有限宇宙中探测、通讯、签约、背叛、威慑、打击——验证"暴露即毁灭，隐藏即生存"。

---

## 理论基础

> 宇宙就是一座黑暗森林，每个文明都是带枪的猎人。如果他发现了别的生命，能做的只有一件事：开枪消灭之。

**两大公理：**
1. 生存是文明的第一需要
2. 文明不断增长和扩张，但宇宙物质总量保持不变

**两大概念：**
- **猜疑链** — 你无法确定对方是否善意，对方也不知道你是否善意，无限递归
- **技术爆炸** — 弱小文明可能在短时间内技术飞跃，颠覆格局

---

## 五种文明

| 策略 | 颜色 | 行为 |
|------|------|------|
| 🔵 隐藏者 | 蓝 | 极限隐蔽，暗中科研。被威胁时反击 |
| 🔴 侵略者 | 红 | 发现即打击，扩张优先。不重复攻击 |
| 🟢 外交家 | 绿 | 通讯建交，签约结盟。被背叛后变隐藏者 |
| 🟡 观察者 | 黄 | 暗中探测，记录沉默。不广播不外交 |
| 🟣 清理者 | 紫 | 监听广播，光粒清除。100% 响应广播信号 |

---

## 核心机制

| 系统 | 描述 |
|------|------|
| 探测系统 | 主动探测 + 被动暴露 + 广播全局可见 |
| 战斗系统 | 光粒（无限距）/ 二向箔（暴露科技）/ 常规打击 |
| 外交系统 | 通讯 → 互不侵犯 → 贸易 → 军事同盟 |
| 威慑系统 | "敢打我，我就广播你的坐标"——同归于尽博弈 |
| 咒语系统 | 广播别人坐标，让第三方清理者代劳打击 |
| 猜疑链 | 多疑度属性 + 信任骰子，影响条约成功率 |
| 技术爆炸 | 小概率突破事件，弱者可能翻盘 |
| 军备竞赛 | 互相探测 → ALERT → 扩军 → 冷和平 |
| 连锁暴露 | 攻击/突破/摧毁都会暴露位置 |
| 策略切换 | 局势变化时文明自动改变策略 |

---

## 快速开始

```bash
# 安装依赖
pip install fastapi uvicorn pydantic websockets

# 启动服务
cd dark-forest
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 浏览器打开
# http://localhost:8000
```

**命令行模式：**

```python
from engine.runner import SimulationRunner
from engine.config import SimulationConfig

config = SimulationConfig(
    universe_width=300, max_turns=200,
    hider_count=4, aggressor_count=3, diplomat_count=2,
    observer_count=2, cleaner_count=1,
)
runner = SimulationRunner(config)
history = runner.run_simulation()

final = history[-1]
for c in final['civilizations']:
    status = '存活' if not c['is_destroyed'] else '毁灭'
    print(f"{c['name']}: {status} ({c['turns_alive']}回合) 击杀{c['kill_count']}")
```

---

## 项目结构

```
dark-forest/
├── engine/                     # Python 模拟引擎
│   ├── core/                   # 基础层: 坐标/枚举/事件/状态机
│   ├── civ/                    # 文明层: 聚合根/组件/策略/工厂
│   ├── systems/                # 系统层: 9个纯逻辑系统
│   ├── universe.py             # 宇宙容器 (Mediator)
│   ├── runner.py               # 回合编排器
│   └── config.py               # 参数配置
├── api/main.py                 # FastAPI 接口 (REST)
├── web/index.html              # Canvas 星图可视化
├── tests/                      # 测试
├── scenarios/                  # 预设场景
└── requirements.txt
```

### 设计模式

| 模式 | 用途 |
|------|------|
| Strategy | 5 种文明策略独立类，加新策略不改旧代码 |
| Component | 经济/军事/外交/记忆 按领域拆分 |
| Mediator | Universe 统一协调所有文明交互 |
| Observer | EventBus + 10 种类型化事件 |
| State Machine | 文明 6 态流转（和平/警戒/威慑/战争/同盟） |
| Builder | CivilizationFactory 文明工厂 |

---

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/scenarios` | 预设场景列表 |
| POST | `/api/simulations` | 创建新模拟 |
| GET | `/api/simulations/{id}` | 当前状态 |
| POST | `/api/simulations/{id}/step` | 推进一回合 |
| POST | `/api/simulations/{id}/run` | 运行至结束 |
| GET | `/api/simulations/{id}/history` | 完整历史 |
| POST | `/api/scenarios/{id}/run` | 运行预设场景 |

---

## 运行测试

```bash
PYTHONPATH=. python3 tests/test_v2_smoke.py
```

---

## 扩展指南

添加新策略只需 3 步（不改任何旧代码）：

1. 新建 `engine/civ/strategies/mystrategy.py`，继承 `BaseStrategy`
2. 在 `engine/civ/factory.py` 的 `_STRATEGY_CLASSES` 和名字池注册
3. 在 `engine/core/enums.py` 的 `Strategy` 枚举添加值

添加新系统只需 2 步：

1. 新建 `engine/systems/newsystem.py`，实现纯函数
2. 在 `engine/core/events.py` 添加新事件类型
3. 在 `engine/runner.py` 的 `_execute()` 中注册新 Action
