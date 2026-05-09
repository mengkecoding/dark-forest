# 交付测试清单

## 1. 引擎层（命令行）

- [ ] 编译检查：所有 Python 文件通过 py_compile
- [ ] 单元测试：3 条 smoke test 通过
- [ ] 模拟可运行：创建 SimulationRunner，运行 50 回合，有 snapshot 输出
- [ ] 战斗发生：运行后有 kill_count > 0 的文明
- [ ] 清理者响应广播：存在清理者打击广播者的日志
- [ ] 外交通信：存在通信/条约相关日志
- [ ] 技术爆炸：存在科技突破日志
- [ ] 模拟不卡死：200 回合内不出现连续 80 回合无事

## 2. API 层（curl）

- [ ] GET /api/health → 200
- [ ] GET /api/scenarios → 返回 3 个场景
- [ ] POST /api/simulations → 201，返回 sim_id
- [ ] POST /api/simulations/{id}/step → 200
- [ ] POST /api/simulations/{id}/run → 200，返回 history
- [ ] GET / → 返回 HTML

## 3. 前端层（浏览器）

- [ ] 页面加载：不显示"后端未启动"
- [ ] 自动创建模拟：显示文明列表和星图
- [ ] 按钮状态：单步/动画运行 按钮可用（非 disabled）
- [ ] 点击「新建」：创建新模拟
- [ ] 点击「动画运行」：逐帧播放
- [ ] 点击「停止」：播放停止
- [ ] 点击文明：高亮选中
- [ ] 事件日志：显示中文事件（战斗/广播/条约等）

## 4. 集成测试

- [ ] 引擎 + API 联调：通过 API 创建模拟 → step 推进 → run 完成
- [ ] 前端 + API 联调：浏览器打开 → 自动创建模拟 → 动画运行
