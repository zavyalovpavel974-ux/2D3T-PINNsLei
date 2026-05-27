# 学习笔记：`train()` 与 2D 3T PINNs 的总损失构造

## 作用

`train()` 是作者把所有物理约束和训练约束组合成一个总优化目标的地方。

前一份笔记中，`net_f()` 已经构造出了三个 PDE 残差：

```text
fe, fi, fr
```

在 `train()` 中，作者把这些 PDE 残差与以下约束组合起来：

- 初始条件损失；
- 光子上边界 Dirichlet 损失；
- Neumann / 零通量边界损失；
- 对数损失；
- 人工加权；
- Adam 与 L-BFGS 两阶段优化。

对应文件：

```text
sub_2D3T_wei_aei700_wer_krartr_time.py
```

函数入口：

```python
def train(self, nIter, X_star):
```

这套训练逻辑服务于 Example 5 的正问题路径：

```text
Aei = 70 -> 400 -> 700
Kr = Ar * Tr
```

## 第 1 步：创建优化器

代码中创建了两个优化器：

```python
opt = torch.optim.Adam(
    self.net_u.parameters(),
    lr=args.lr,
    betas=(0.9, 0.999),
    weight_decay=args.weight_decay
)

opt_lbfgs = torch.optim.LBFGS(
    self.net_u.parameters(),
    lr=1.2,
    tolerance_change=1e-302,
    tolerance_grad=1e-302,
    history_size=120,
    max_iter=30000,
    line_search_fn='strong_wolfe'
)
```

训练分成两个阶段：

```text
先 Adam
后 L-BFGS
```

学习率衰减器是：

```python
scheduler = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=args.lr_decay)
```

在主程序里，Adam 通常训练约 `6000` 次，L-BFGS 最多训练 `30000` 次。这和论文实验设置一致。

## 第 2 步：选择基础损失函数

代码支持三类基础损失：

```python
if args.which_loss == 1:
    loss_func = torch.nn.MSELoss()
elif args.which_loss == 2:
    loss_func = torch.nn.L1Loss()
else:
    loss_func = torch.nn.SmoothL1Loss()
```

默认使用：

```text
MSELoss
```

因此多数约束项本质上都是均方误差惩罚。

## 第 3 步：定义光子上边界条件

在 `train()` 内部，作者定义了：

```python
def Trfree_boundary(x, t):
    u = 3e-4 + 2*t
    return u
```

这对应论文中的光子上边界 Dirichlet 条件：

```text
y = 1:
Tr = 3e-4 + 2t
```

这个边界非常关键，因为它相当于热量进入计算区域的驱动边界。

## 第 4 步：核心闭包 `complus_loss()`

`train()` 的核心是内部闭包函数：

```python
def complus_loss(it=None):
```

它负责：

```text
计算当前总损失
执行反向传播
把 loss 返回给优化器
```

Adam 和 L-BFGS 都会调用这个闭包。

### 初始点预测

```python
u0_pred = self.net(torch.cat((self.x_t0, self.y_t0, self.t_t0), 1))
```

这些点位于：

```text
t = 0
```

期望满足初始条件：

```text
Te = Ti = Tr = 3e-4
```

### 上边界预测

```python
urg3_pred = self.net(torch.cat((self.x_yub, self.y_yub, self.t_yub), 1))
```

这些点位于：

```text
y = 1
```

其中光子温度应满足：

```text
Tr = 3e-4 + 2t
```

### 边界导数条件

```python
ret_Tr3 = self.net_dtdnr(...)
ret_TeTi8 = self.net_dtdnei(...)
```

这两个函数负责计算边界导数残差。

`ret_Tr3` 包含 3 个光子边界导数残差，用于约束光子温度在相关边界上的 Neumann / 零通量条件。

`ret_TeTi8` 包含 8 个电子、离子边界导数残差，用于约束电子和离子温度的零通量边界条件。

因为这些导数约束的目标值都是 0，所以法向导数的正负号对 MSE 损失本身不重要。

### PDE 残差

```python
fe, fi, fr = ret_f = self.net_f(
    self.x_f,
    self.y_f,
    self.t_f,
    self.rou,
    self.ce,
    self.ci,
    self.cr,
    self.beta,
    self.Ae,
    self.Ai,
    self.Ar,
    self.Aei,
    self.Aer
)
```

这三个量是内部残差点上的三温方程残差：

```text
fe：电子温度方程残差
fi：离子温度方程残差
fr：光子温度方程残差
```

训练目标是：

```text
fe = 0
fi = 0
fr = 0
```

## 第 5 步：PDE 残差损失

代码中先计算：

```python
lossfe = loss_func(fe, torch.zeros_like(fe))
lossfi = loss_func(fi, torch.zeros_like(fi))
lossfr = loss_func(fr, torch.zeros_like(fr))
```

也就是：

```text
MSE(fe, 0)
MSE(fi, 0)
MSE(fr, 0)
```

这些项负责让网络预测解在内部残差点上满足控制方程。

## 第 6 步：初始条件的对数损失

当前激活的损失表达式中包含：

```python
10 * loss_func(torch.log(u0_pred[:,0:1]), torch.log(t0 * torch.ones_like(u0_pred[:,0:1])))
10 * loss_func(torch.log(u0_pred[:,1:2]), torch.log(t0 * torch.ones_like(u0_pred[:,1:2])))
10 * loss_func(torch.log(u0_pred[:,2:3]), torch.log(t0 * torch.ones_like(u0_pred[:,2:3])))
```

其中：

```python
t0 = 3e-4
```

这对应论文中的“初始条件损失取对数”技术。

为什么要取对数？

初始温度非常小：

```text
3e-4
```

而后期温度可能达到 `O(1)`。如果直接使用普通 MSE，初始条件误差在数值上很容易被其他大尺度损失淹没。取对数后，小温度处的相对误差会更明显。

这三个损失项约束的是：

```text
log(Te(x,y,0)) ≈ log(3e-4)
log(Ti(x,y,0)) ≈ log(3e-4)
log(Tr(x,y,0)) ≈ log(3e-4)
```

三项初始条件损失的权重均为：

```text
10
```

## 第 7 步：光子 Dirichlet 上边界的对数损失

当前激活的损失表达式中还包含：

```python
20 * loss_func(
    torch.log(urg3_pred[:,2:3]),
    torch.log(Trfree_boundary(self.x_yub, self.t_yub))
)
```

它约束的是：

```text
y = 1:
Tr = 3e-4 + 2t
```

这里同样使用对数损失，因为该边界值在早期也从 `3e-4` 这样的很小量级开始，随后随时间增大。

该项权重为：

```text
20
```

这体现了论文中反复强调的思想：初始条件和光子 Dirichlet 边界条件需要较合适的权重，否则容易被 PDE 残差项淹没。

## 第 8 步：Neumann / 零通量边界损失

当前激活的损失表达式中包含：

```python
1 * sum([loss_func(TT, torch.zeros_like(TT)) for TT in ret_Tr3])
1 * sum([loss_func(TT, torch.zeros_like(TT)) for TT in ret_TeTi8])
```

这些项约束边界导数条件：

```text
ret_Tr3   -> 光子温度的边界导数残差
ret_TeTi8 -> 电子/离子温度的边界导数残差
```

目标值都是：

```text
normal derivative ≈ 0
```

这些边界导数损失的权重为：

```text
1
```

## 第 9 步：当前激活的总损失

当前真正生效的损失表达式可以概括为：

```python
lossfe = loss_func(fe, torch.zeros_like(fe))
lossfi = loss_func(fi, torch.zeros_like(fi))
lossfr = loss_func(fr, torch.zeros_like(fr))

loss =
    10 * MSE(log(Te_initial), log(3e-4))
  + 10 * MSE(log(Ti_initial), log(3e-4))
  + 10 * MSE(log(Tr_initial), log(3e-4))
  + 20 * MSE(log(Tr_upper_boundary), log(3e-4 + 2t))
  +  1 * photon_derivative_boundary_losses
  +  1 * electron_ion_derivative_boundary_losses
  +      lossfe + lossfi + lossfr
```

更紧凑地说：

```text
total loss =
  初始条件对数损失
+ 光子 Dirichlet 上边界对数损失
+ 零通量 / 边界导数损失
+ PDE 残差损失
```

这一总损失综合体现了论文中的几个关键技术：

- 损失加权；
- 初始条件对数损失；
- 光子边界对数损失；
- PDE 残差约束；
- 边界导数约束。

## 第 10 步：为什么代码里有很多被注释的 loss

你会看到代码中有大量被注释掉的损失表达式。

这些是作者尝试过的不同实验配置，例如：

- 普通初始条件 MSE；
- 更大的光子边界权重，例如 `1000`；
- 不同 PDE 残差权重；
- 不同电子/离子边界项权重；
- 反问题中可能使用的 `lossmu`。

阅读代码时要注意：不要把所有注释块都当成当前生效逻辑。当前 Example 5 生效的是 `lossfe`、`lossfi`、`lossfr` 附近那段未注释的总损失表达式。

## 第 11 步：反向传播

在 `complus_loss()` 接近末尾处：

```python
self.net_u.zero_grad()
loss.backward()
return loss
```

含义是：

```text
清空旧梯度
根据当前总损失计算新梯度
把 loss 返回给优化器
```

因为 L-BFGS 在一次优化步中可能多次调用 loss 函数，所以作者把损失计算写成了闭包 `complus_loss()`。

## 第 12 步：Adam 阶段

第一阶段训练是：

```python
for it in range(start_iter, nIter):
    opt.step(lambda: complus_loss(it))
    scheduler.step()
```

Adam 是第一阶段优化器。

它的作用是先把网络参数推到一个相对合理的区域，再交给 L-BFGS 精细优化。

学习率会通过指数衰减逐步降低：

```text
lr <- lr * gamma
```

其中：

```text
gamma = args.lr_decay
```

默认：

```text
args.lr_decay = 0.999
```

## 第 13 步：L-BFGS 阶段

Adam 结束后，代码执行：

```python
opt_lbfgs.step(complus_loss)
```

L-BFGS 是第二阶段优化器，用于更精细地压低损失。

论文实验设置大致是：

```text
Adam: 6000 iterations
L-BFGS: up to 30000 iterations
```

PINNs 训练中经常采用这种组合：先用 Adam 找到可行区域，再用 quasi-Newton 类型的 L-BFGS 做精修。

## 第 14 步：checkpoint / resume 逻辑

当前本地代码里还包含额外的断点保存和恢复逻辑：

```python
save_checkpoint(...)
maybe_stop_for_walltime(...)
args.resume_checkpoint
```

这些是为了复现管理和长时间运行实验添加的辅助逻辑，不属于论文方法本身的概念核心。

它们的作用是：Example 5 完整训练可能需要数小时，因此需要保存中间状态，方便中断后恢复。

## 与论文技术点的对应关系

| 论文技术 | `train()` 中的体现 |
| --- | --- |
| 损失加权 | 总损失中的系数 `10`、`20`、`1` |
| 初始条件对数损失 | `loss_func(torch.log(u0_pred), torch.log(t0))` |
| 光子 Dirichlet 边界对数损失 | `loss_func(torch.log(urg3_pred[:,2:3]), torch.log(Trfree_boundary(...)))` |
| PDE 残差损失 | `lossfe + lossfi + lossfr` |
| 边界导数约束 | `ret_Tr3` 与 `ret_TeTi8` 对应的损失 |
| Adam + L-BFGS 训练 | `opt.step(...)` 后接 `opt_lbfgs.step(...)` |

需要注意：

Fourier feature embedding 和输出正性约束不在 `train()` 中实现，它们已经写在 `net()` 里。

迁移学习也不在 `train()` 内部实现，而是在主脚本中通过以下训练路径完成：

```text
Aei = 70 -> 400 -> 700
```

每一阶段训练完成后，主脚本会保存网络权重，并在下一阶段加载上一阶段的权重作为初始化。

## 核心理解

`train()` 回答的问题是：

```text
如何强迫神经网络表示一个物理上合理的解？
```

它通过同时满足多类约束实现这一点：

```text
1. 在 t = 0 时，三个温度都应等于 3e-4。
2. 在 y = 1 时，光子温度应等于 3e-4 + 2t。
3. 在其他相关边界上，法向导数 / 通量条件应接近 0。
4. 在区域内部，三个 PDE 残差 fe、fi、fr 应接近 0。
```

所以这个训练过程不是通常意义上的纯监督学习，而是以物理约束为主的学习：

```text
network output
-> initial / boundary / PDE checks
-> weighted total loss
-> Adam and L-BFGS optimize the network
```

## 总体流程图

到这里，正问题 PINNs 的完整主线可以写成：

```text
主脚本采样训练点并设置物理参数
-> PhysicsInformedNN 保存张量并搭建网络
-> net() 使用 Fourier feature 预测正温度 Te, Ti, Tr
-> net_f() 计算 PDE 残差 fe, fi, fr
-> train() 构造加权总损失并优化网络
```

下一步自然要看主脚本中的迁移学习循环：

```text
Aei=70 -> Aei=400 -> Aei=700
```

这一部分对应论文 Example 5 中的 transfer learning strategy。
