# Learning Notes: `net_f()` in the 2D 3T PINNs Code

## Purpose

`net_f()` is the core physics residual function in the author code. It takes
space-time points `(x, y, t)`, asks the neural network to predict the three
temperatures `(Te, Ti, Tr)`, uses PyTorch automatic differentiation to compute
their derivatives, and substitutes everything into the 2-D 3-T heat conduction
equations.

In short:

```text
net()   : (x, y, t) -> (Te, Ti, Tr)
net_f() : (x, y, t) -> (fe, fi, fr)
```

The training objective later tries to make:

```text
fe ≈ 0
fi ≈ 0
fr ≈ 0
```

## Code Location

Main file:

```text
sub_2D3T_wei_aei700_wer_krartr_time.py
```

Function:

```python
def net_f(self, x, y, t, rou, ce, ci, cr, beta, Ae, Ai, Ar, Aei, Aer):
```

This function corresponds to the PDE residual construction for the forward
problem, especially Example 5:

```text
Aei = 700
Kr = Ar * Tr
```

## Step 1: Enable Automatic Differentiation

The function begins with:

```python
x = V(x, requires_grad=True)
y = V(y, requires_grad=True)
t = V(t, requires_grad=True)
```

This tells PyTorch that derivatives with respect to `x`, `y`, and `t` will be
needed.

The PDE contains terms such as:

```text
∂Te/∂t, ∂Ti/∂t, ∂Tr/∂t
∂/∂x(K ∂T/∂x)
∂/∂y(K ∂T/∂y)
```

Therefore, the coordinates must participate in the computational graph.

## Step 2: Predict the Three Temperatures

The code calls the neural network:

```python
Te, Ti, Tr = torch.split(self.net(torch.cat([x, y, t], 1)), 1, 1)
```

Meaning:

```text
input  = (x, y, t)
output = (Te, Ti, Tr)
```

Here:

- `Te` is electron temperature.
- `Ti` is ion temperature.
- `Tr` is photon/radiation temperature.

The earlier `net()` function already includes:

- input normalization,
- Fourier feature embedding,
- positive output constraint using `softplus`.

## Step 3: Compute First-Order Derivatives

The code computes:

```python
Te_x, Te_y, Te_t = self._grad_(Te, [x, y, t])
Ti_x, Ti_y, Ti_t = self._grad_(Ti, [x, y, t])
Tr_x, Tr_y, Tr_t = self._grad_(Tr, [x, y, t])
```

These are:

```text
Te_x = ∂Te/∂x
Te_y = ∂Te/∂y
Te_t = ∂Te/∂t

Ti_x = ∂Ti/∂x
Ti_y = ∂Ti/∂y
Ti_t = ∂Ti/∂t

Tr_x = ∂Tr/∂x
Tr_y = ∂Tr/∂y
Tr_t = ∂Tr/∂t
```

The helper function is:

```python
def _grad_(self, y, x):
    return torch.autograd.grad(
        y,
        x,
        torch.ones_like(y),
        create_graph=True,
        retain_graph=True
    )
```

`create_graph=True` is important because second-order derivative structures are
needed later.

## Step 4: Define Conductivities

For Example 5, the code uses:

```python
Ke, Ki, Kr = Ae * Te.pow(5/2), Ai * Ti.pow(5/2), Ar * Tr
```

This corresponds to Table 2 of the paper:

```text
Ke = Ae * Te^(5/2)
Ki = Ai * Ti^(5/2)
Kr = Ar * Tr
```

The code also contains commented alternatives:

```python
# Kr = Ar
# Kr = Ar * Tr.pow(3 + beta)
```

These correspond to easier or harder variants discussed in the paper:

- `Kr = Ar` for Example 2 and Example 3.
- `Kr = Ar * Tr` for Example 4 and Example 5.
- `Kr = Ar * Tr^(3+β)` for a harder case the current method cannot solve well.

## Step 5: Define Coupling Coefficients

The code uses:

```python
wei, wer = rou * Aei * Te.pow(-2/3), rou * Aer * Te.pow(-1/2)
```

This corresponds to Table 2:

```text
ωei = Aei * ρ * Te^(-2/3)
ωer = Aer * ρ * Te^(-1/2)
```

Physical meaning:

- `wei` controls electron-ion energy exchange.
- `wer` controls electron-photon energy exchange.

This also explains why the positive output constraint is necessary. If `Te` is
non-positive, terms like `Te^(-2/3)` and `Te^(-1/2)` can cause invalid values
or `NaN`.

## Step 6: Compute Diffusion Terms

The diffusion terms are:

```python
Nb_e = self._grad_(Ke * Te_x, x)[0] + self._grad_(Ke * Te_y, y)[0]
Nb_i = self._grad_(Ki * Ti_x, x)[0] + self._grad_(Ki * Ti_y, y)[0]
Nb_r = self._grad_(Kr * Tr_x, x)[0] + self._grad_(Kr * Tr_y, y)[0]
```

Mathematically:

```text
Nb_e = ∂/∂x(Ke ∂Te/∂x) + ∂/∂y(Ke ∂Te/∂y)
Nb_i = ∂/∂x(Ki ∂Ti/∂x) + ∂/∂y(Ki ∂Ti/∂y)
Nb_r = ∂/∂x(Kr ∂Tr/∂x) + ∂/∂y(Kr ∂Tr/∂y)
```

That is:

```text
Nb_e = ∇ · (Ke ∇Te)
Nb_i = ∇ · (Ki ∇Ti)
Nb_r = ∇ · (Kr ∇Tr)
```

The code does not use finite differences here. These derivatives come from
PyTorch automatic differentiation.

## Step 7: Electron Residual `fe`

Code:

```python
feleft = ce * Te_t - 1 / rou * Nb_e
feright = wei * (Ti - Te) + wer * (Tr - Te)
fe = feleft - feright
```

Mathematically:

```text
fe =
ce ∂Te/∂t
- (1/ρ) ∇·(Ke ∇Te)
- [ωei(Ti - Te) + ωer(Tr - Te)]
```

Training target:

```text
fe ≈ 0
```

Physical interpretation:

```text
electron temperature evolution
= electron heat diffusion
+ electron-ion exchange
+ electron-photon exchange
```

## Step 8: Ion Residual `fi`

Code:

```python
fileft = ci * Ti_t - 1 / rou * Nb_i
firight = wei * (Te - Ti)
fi = fileft - firight
```

Mathematically:

```text
fi =
ci ∂Ti/∂t
- (1/ρ) ∇·(Ki ∇Ti)
- ωei(Te - Ti)
```

Training target:

```text
fi ≈ 0
```

The ion equation exchanges energy with electrons, but not directly with photons.

## Step 9: Photon Residual `fr`

Code:

```python
frleft = cr * Tr.pow(3) * Tr_t - 1 / rou * Nb_r
frright = wer * (Te - Tr)
fr = frleft - frright
```

Mathematically:

```text
fr =
cr Tr^3 ∂Tr/∂t
- (1/ρ) ∇·(Kr ∇Tr)
- ωer(Te - Tr)
```

Training target:

```text
fr ≈ 0
```

The photon equation includes the nonlinear time term:

```text
Tr^3 * ∂Tr/∂t
```

## Step 10: Return the Residuals

The function ends with:

```python
return fe, fi, fr
```

`net_f()` does not directly compute the loss. It returns the residuals. The
training function later computes:

```python
lossfe = loss_func(fe, torch.zeros_like(fe))
lossfi = loss_func(fi, torch.zeros_like(fi))
lossfr = loss_func(fr, torch.zeros_like(fr))
```

So the PDE loss is essentially:

```text
MSE(fe, 0) + MSE(fi, 0) + MSE(fr, 0)
```

## Mapping to Paper Table 2

| Paper expression | Code |
| --- | --- |
| `ωei = Aei ρ Te^(-2/3)` | `wei = rou*Aei*Te.pow(-2/3)` |
| `ωer = Aer ρ Te^(-1/2)` | `wer = rou*Aer*Te.pow(-1/2)` |
| `Ke = Ae Te^(5/2)` | `Ke = Ae*Te.pow(5/2)` |
| `Ki = Ai Ti^(5/2)` | `Ki = Ai*Ti.pow(5/2)` |
| `Kr = Ar Tr` | `Kr = Ar*Tr` |

## Core Intuition

`net_f()` is a physics checker:

```text
1. Pick a point (x, y, t).
2. Use the neural network to predict (Te, Ti, Tr).
3. Use automatic differentiation to compute derivatives.
4. Substitute everything into the 2-D 3-T heat conduction equations.
5. Return residuals (fe, fi, fr).
```

If the network perfectly satisfies the PDE:

```text
fe = 0
fi = 0
fr = 0
```

During training, the optimizer adjusts the neural network so these residuals
become small at the sampled collocation points.

## Big Picture

At this point, the main PINNs pipeline is:

```text
main script creates training points
→ PhysicsInformedNN stores points and physical parameters
→ net() predicts Te, Ti, Tr
→ net_f() computes PDE residuals fe, fi, fr
→ train() combines PDE residuals, initial loss, boundary loss, and weights
```

The next concept to study is `train()`, where the author combines:

- PDE residual losses,
- initial condition losses,
- boundary condition losses,
- normal-derivative boundary losses,
- logarithmic loss,
- manual weights,
- Adam and L-BFGS optimization.
