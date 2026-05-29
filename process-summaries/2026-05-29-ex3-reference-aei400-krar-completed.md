# Ex3 参考解求解记录 (Aei=400, Kr=Ar)

**求解状态**
- 状态：正常完成
- 方法：20×20 求解 + 线性插值到 80×80
- 耗时：20.4 秒，81 步
- 退出原因：正常完成（t=1.0 到达）

**求解配置**
- case: aei400_krar
- Aei: 400.0
- kr_power: 0.0 (常数 Kr)
- 网格: 20×20, cell_center
- dt_init: 5e-3
- dt_min: 1e-6
- dt_max: 2e-2
- newton_tol: 1e-3
- newton_max: 8
- gmres_maxiter: 120

**输出文件**
- 20×20 原始解: reference_solver_outputs/aei400_krar_20/outputs/reference_snapshots.npz
- 80×80 插值解: reference_solver_outputs/aei400_krar_20/outputs/reference_snapshots_80x80_from20.npz
- author txt 文件: reference_solver_outputs/aei400_krar_20/outputs/author_txt_80x80/
  - sol1_wei_aei400_wer_krar_1e-5.txt
  - sol1_wei_aei400_wer_krar_0p3.txt
  - sol1_wei_aei400_wer_krar_0p5.txt
  - sol1_wei_aei400_wer_krar_0p7.txt
  - sol1_wei_aei400_wer_krar_1.txt

**验证结果**
- 所有时刻 Te/Ti/Tr 值有限 (finite=true)
- 上边界 Tr 值正确 (t0+2t)
- 物理值范围合理:
  - t=0.00001: Te=0.0003, Ti=0.0003, Tr=0.0003~0.00032
  - t=0.3: Te=0.096~0.155, Ti=0.076~0.120, Tr=0.363~0.600
  - t=0.5: Te=0.210~0.291, Ti=0.167~0.230, Tr=0.707~1.000
  - t=0.7: Te=0.344~0.436, Ti=0.276~0.351, Tr=1.070~1.400
  - t=1.0: Te=0.577~0.666, Ti=0.465~0.545, Tr=1.631~2.000

**与 80×80 直接求解的对比**
- 80×80 直接求解因刚性问题失败 (dt<1e-10 at t=0.007746)
- 20×20 求解成功，插值到 80×80 用于 pipeline validation
- 注意：插值版精度 = 20×20，非论文级精度

**下一步**
- 用 80×80_from20 参考解补算 Ex3 PINN metrics
- 继续 Ex4 (aei400_krartr) 参考解求解

**记录时间**
- 2026-05-29 00:53 CST
