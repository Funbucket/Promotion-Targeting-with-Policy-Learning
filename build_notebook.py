"""
who_should_be_treated_ko.ipynb 빌더.

질문 기반(Q1~Q5) 구조 + Executive Summary + 결론/권고로 노트북을 생성한다.
마크다운은 한국어 보고서 어조, 코드 셀은 분석 코드 + 백서용 figure 저장.

사용: python build_notebook.py  ->  who_should_be_treated_ko.ipynb
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


# ---------------------------------------------------------------- 표지
md(r"""
# 누구에게 어떤 프로모션을 제공해야 할까?
### 예산 제약 하의 정책학습(Policy Learning) 기반 프로모션 타겟팅

<small><em>Written by Haechang Cho · <a href="https://github.com/Funbucket">GitHub</a> · <a href="https://www.linkedin.com/in/hae-chang-cho/">LinkedIn</a></em></small>
""")

# ---------------------------------------------------------------- Executive Summary
md(r"""
## 요약 (Executive Summary)

**문제.** 한 소프트웨어 회사는 고객에게 *기술지원*과 *할인* 두 가지 프로모션을 제공할 수 있습니다(두 개입의 조합으로 총 4가지 처치). 예산은 제한되어 있고, 프로모션 효과는 고객마다 다릅니다. 따라서 핵심 질문은 다음과 같습니다.

> **"제한된 예산 안에서 누구에게 어떤 프로모션을 제공해야 전체 순이익이 가장 커질까?"**

**접근.** 약 2,000명의 **관찰 데이터**에 정책학습(policy learning)을 적용했습니다. ① 처치 효과의 이질성을 진단하고, ② 관찰 데이터의 인과 식별 가정을 점검한 뒤, ③ 세 가지 정책(DRLearner plug-in · DRPolicyTree · DRPolicyForest)을 학습하고, ④ 학습/평가 데이터를 분리해 **AIPW(doubly robust) score**로 정책 가치를 비교했으며, ⑤ 예산 제약 하의 효율은 **비용 곡선(cost curve)**으로 평가했습니다.

**핵심 결과.**

| | 1인당 평균 순이익 | 무처치 대비 |
| --- | ---: | ---: |
| 무처치 (all none) | \$7,249 | — |
| 최선의 단일 처치 (전원 기술지원) | \$10,527 | +45% |
| **고객별 타겟팅 (DRLearner plug-in)** | **\$11,798** | **+63%** |

- 고객별 타겟팅 정책은 가장 좋은 **단일 처치 정책보다 약 12%**, 무처치 대비 약 63% 높은 순이익을 냈습니다.
- 처치 배정을 좌우한 핵심 요인은 **직원 수(42%)와 고객 규모(38%)**였습니다. 규모가 큰 고객에게는 *기술지원+할인*을, 그 외 고객에게는 주로 *기술지원*을 배정했습니다.
- **예산 수준에 따라 최적 정책이 달랐습니다.** 소액 예산에서는 평균 비용이 낮은 *전원 기술지원*이 가장 효율적이지만, 예산이 1인당 \$4,000~6,000 수준으로 커지면 학습 정책이 더 높은 순이익을 냈습니다.

**권고.** 모두에게 동일한 프로모션을 적용하기보다, **고객 규모·직원 수에 기반한 타겟팅 규칙**을 적용할 것을 권고합니다. 성능을 최우선한다면 plug-in/forest 정책을, 이해관계자 설명과 운영 안정성이 중요하다면 약간의 성능을 양보하더라도 해석 가능한 **depth=2 의사결정 트리 정책**을 권장합니다(자세한 내용은 마지막 "결론 및 권고" 절 참조).
""")

# ---------------------------------------------------------------- 1. 비즈니스 문제
md(r"""
## 1. 비즈니스 문제

인과추론의 많은 문제는 평균 처치 효과(ATE)에 집중합니다. "프로모션을 진행할 것인가, 하지 않을 것인가?"라는 질문은 **모든 고객에게 동일한** 프로모션을 제공하는 정책과 아무에게도 제공하지 않는 정책을 비교하는 문제입니다.

하지만 예산이 제한되어 있고 그 안에서 최대 효과를 내야 한다면 이야기가 달라집니다. 프로모션 효과가 고객마다 다르다면, 모두에게 동일하게 제공하는 전략이 최선이 아닐 수 있습니다.

- 마케팅 유무와 상관없이 어차피 구매하거나(*always-converters*), 반대로 아무리 혜택을 줘도 사지 않을 고객(*lost causes*)에게 불필요한 예산을 낭비하게 됩니다.
- 마케팅에 부정적으로 반응하는 고객(*sleeping dogs*) 때문에 오히려 손실이 발생하며,
- 정작 효과가 클 고객(*high-responders*)을 우선순위에 두지 못해 잠재 매출을 놓칩니다.

따라서 이 분석이 답하려는 질문은 다음과 같습니다.

> _"어떤 고객을 대상으로 해야 순이익이 가장 커질까?"_

가능한 처치 규칙들을 탐색해 전체 평균 순수익을 근사적으로 최대화하는 문제, 즉 **"누구를 처치해야 하는가?"**에 답하는 문제를 다룹니다. 이를 **정책학습(policy learning)**이라고 부릅니다.

이 분석은 다음 다섯 가지 질문으로 구성됩니다.

1. **Q1.** 프로모션 효과는 정말 고객마다 다른가? (이질성 진단)
2. **Q2.** 관찰 데이터로 인과 효과를 신뢰할 수 있는가? (식별 가정)
3. **Q3.** 누구에게 무엇을 배정해야 하는가? (정책학습)
4. **Q4.** 학습한 정책이 정말 더 나은가? (정책 평가)
5. **Q5.** 예산이 제한되면 어떤 정책이 유리한가? (예산 제약)
""")

md(r"""<img src="./assets/AJStyles&Undertaker.jpg" width="480"/>

<small>같은 자극(프로모션)에도 사람마다 반응이 다릅니다. 정책학습은 "누구에게 효과가 큰가"를 데이터로 찾습니다.</small>""")

code(r"""
import os
import tempfile
import warnings
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

from econml.dr import DRLearner
from econml.policy import DRPolicyForest, DRPolicyTree

warnings.filterwarnings('ignore')

# 백서(PDF)용 figure 저장 경로
FIGDIR = Path('figures')
FIGDIR.mkdir(exist_ok=True)
SAVE_KW = dict(dpi=150, bbox_inches='tight')

SEED = 1
rng = np.random.default_rng(SEED)
np.random.seed(SEED)
sns.set_theme(style='whitegrid')
""")

# ---------------------------------------------------------------- 2. 데이터와 처치 정의
md(r"""
## 2. 데이터와 처치 정의

한 소프트웨어 판매 회사는 할인이나 기술지원 같은 프로모션이 고객의 소프트웨어 구매를 실제로 늘리는지, 그리고 어떤 고객에게 더 효과적인지 알고 싶어합니다.

고객마다 서로 다른 프로모션을 무작위로 배정하는 실험(RCT)이 가장 이상적이지만, 실제 비즈니스 환경에서는 비용 문제, 영업 전략, 대형 고객을 놓칠 위험 등으로 무작위 실험을 수행하기 어렵습니다. 따라서 이번 데이터는 무작위 실험 데이터가 아닌 **관찰 데이터**입니다.

데이터에는 약 2,000명의 고객 정보가 포함되며, 다음과 같은 변수들로 구성됩니다.

- **고객 특성:** 산업 분야, 규모, 매출, 기술 프로필
- **개입:** 고객에게 제공된 프로모션
- **결과:** 프로모션 제공 이후 1년 동안의 소프트웨어 구매 금액

| 변수명 | 타입 | 설명 |
| --- | -- | --- |
| Global Flag | X | 글로벌 오피스(해외 지사) 보유 여부 |
| Major Flag | X | 해당 산업의 대규모 소비 고객 여부 |
| SMC Flag | X | 중소기업(SMC) 여부 |
| Commercial Flag | X | 사업 유형이 상업용인지 여부 |
| IT Spend | X | IT 관련 구매 금액 |
| Employee Count | X | 직원 수 |
| PC Count | X | 사용 PC 수 |
| Size | X | 연간 총매출 기준 고객 규모 |
| Tech Support | T | 기술지원 제공 여부 (이진값) |
| Discount | T | 할인 제공 여부 (이진값) |
| Revenue | Y | 소프트웨어 구매 금액 기준 매출 |

`Tech Support`와 `Discount`는 모두 개입이므로, 이를 조합해 네 가지 처치로 정의합니다.

$$A_i \in \{0, 1, 2, 3\}$$

- $A_i = 0$: 아무 개입도 제공하지 않음 (none)
- $A_i = 1$: 기술지원만 제공 (tech_support_only)
- $A_i = 2$: 할인만 제공 (discount_only)
- $A_i = 3$: 기술지원과 할인을 모두 제공 (discount_plus_support)
""")

code(r"""
data = pd.read_csv('./data/multi_attribution_sample.csv')
data.columns = data.columns.str.strip()

covariates = [
    'Global Flag',
    'Major Flag',
    'SMC Flag',
    'Commercial Flag',
    'IT Spend',
    'Employee Count',
    'PC Count',
    'Size',
]
outcome = 'Revenue'

TREATMENT_NAMES = {
    0: 'none',
    1: 'tech_support_only',
    2: 'discount_only',
    3: 'discount_plus_support',
}
TREATMENT_LABELS = [TREATMENT_NAMES[i] for i in range(4)]

required_columns = covariates + ['Tech Support', 'Discount', outcome]
for col in required_columns:
    data[col] = pd.to_numeric(data[col], errors='coerce')

policy_df = data[required_columns].dropna().copy()
policy_df['treatment'] = (
    2 * policy_df['Discount'].astype(int)
    + policy_df['Tech Support'].astype(int)
).astype(int)
policy_df['treatment_name'] = policy_df['treatment'].map(TREATMENT_NAMES)

n = len(policy_df)
X = policy_df[covariates].to_numpy()
Y = policy_df[outcome].to_numpy(dtype=float)
A = policy_df['treatment'].to_numpy(dtype=int)

print(policy_df.shape)
policy_df.head()
""")

# ------ 비용 설정
md(r"""
### 2.1. 비용 설정

수익 극대화를 위해서는 매출과 함께 **비용**도 고려해야 합니다. 또한 동일한 프로모션이라도 고객 특성에 따라 비용이 달라질 수 있습니다. 예를 들어 기술지원은 직원 수가 많은 기업일수록 더 많은 지원 시간이 필요하고, 할인은 규모가 큰 고객일수록 더 큰 할인 폭을 요구할 수 있습니다.

이 데이터에는 실제 비용 정보가 없으므로, 고객 특성에 따라 달라지는 비용을 **시뮬레이션**해 사용합니다. 기술지원 비용은 직원 수가 많을수록, 할인 비용은 고객 규모가 클수록 증가하도록 설정합니다. 로그정규분포를 사용해 비용이 항상 양수이고 일부 고객에서 큰 비용이 발생하는 분포를 반영합니다.

$$C_i(\text{tech}) \sim \text{LogNormal}(\log C_{\text{tech}} + 0.5 \cdot \tilde{e}_i,\ 0.3), \qquad C_i(\text{disc}) \sim \text{LogNormal}(\log C_{\text{disc}} + 0.4 \cdot \tilde{s}_i,\ 0.3)$$

여기서 $\tilde{e}_i$는 표준화된 직원 수, $\tilde{s}_i$는 표준화된 회사 규모입니다. 고객별 비용을 반영한 최종 **순이익(net outcome)**은 다음과 같습니다.

$$Y_i^{net} = Y_i - C_i(A_i)$$

이렇게 하면 이후 AIPW score가 순이익 기준으로 계산되어, 비용을 고려한 정책 최적화와 평가가 가능해집니다.
""")

code(r"""
COST_TECH_SUPPORT = 4_000.0   # baseline cost for tech support
COST_DISCOUNT     = 5_000.0   # baseline  cost for discount


rng_c = np.random.default_rng(SEED + 99)
emp_idx  = covariates.index('Employee Count')
size_idx = covariates.index('Size')

emp_z  = (X[:, emp_idx]  - X[:, emp_idx].mean())  / (X[:, emp_idx].std()  + 1e-8)
size_z = (X[:, size_idx] - X[:, size_idx].mean()) / (X[:, size_idx].std() + 1e-8)

c_tech = rng_c.lognormal(mean=np.log(COST_TECH_SUPPORT) + 0.5 * emp_z, sigma=0.3)
c_disc = rng_c.lognormal(mean=np.log(COST_DISCOUNT) + 0.4 * size_z, sigma=0.3)

c_tech = np.clip(c_tech, 200.0, 40_000.0)
c_disc = np.clip(c_disc, 200.0, 30_000.0)

C_obs = np.select(
    [A == 1, A == 2, A == 3],
    [c_tech, c_disc, c_tech + c_disc],
    default=0.0,
)

Y_net = Y - C_obs

pd.DataFrame({
    'treatment': TREATMENT_LABELS,
    'mean_cost':  [C_obs[A == a].mean() if (A == a).sum() > 0 else 0.0 for a in range(4)],
    'std_cost':   [C_obs[A == a].std()  if (A == a).sum() > 0 else 0.0 for a in range(4)],
    'mean_revenue':     [Y[A == a].mean()     for a in range(4)],
    'mean_net_revenue': [Y_net[A == a].mean() for a in range(4)],
})
""")

code(r"""
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

sns.histplot(c_tech, bins=30, stat='density', element='step', fill=True, ax=axes[0], color='tab:blue')
axes[0].axvline(np.median(c_tech), color='black', ls='--', lw=1, alpha=0.7)
axes[0].set_title('Tech support cost distribution')
axes[0].set_xlabel('Cost')
axes[0].set_ylabel('Density')
axes[0].set_xlim(left=0)

sns.histplot(c_disc, bins=30, stat='density', element='step', fill=True, ax=axes[1], color='tab:orange')
axes[1].axvline(np.median(c_disc), color='black', ls='--', lw=1, alpha=0.7)
axes[1].set_title('Discount cost distribution')
axes[1].set_xlabel('Cost')
axes[1].set_ylabel('Density')
axes[1].set_xlim(left=0)

plt.suptitle('Simulated cost distributions', y=1.02)
plt.tight_layout()
plt.savefig(FIGDIR / 'fig01_cost_dist.png', **SAVE_KW)
plt.show()
""")

# ------ 데이터 분할
md(r"""
### 2.2. 데이터 분할

정책학습과 평가를 같은 데이터로 수행하면 과대추정이 발생할 수 있습니다. 따라서 데이터를 train/test로 나눠 **학습과 평가를 분리**합니다.
""")

code(r"""
idx = np.arange(len(policy_df))
train_idx, test_idx = train_test_split(
    idx,
    test_size=0.5,
    stratify=A,
    random_state=SEED,
)

X_train = X[train_idx]
X_test = X[test_idx]
A_train = A[train_idx]
A_test = A[test_idx]
Y_net_train = Y_net[train_idx]
Y_net_test = Y_net[test_idx]

print(f"Train: {len(train_idx)} \nTest: {len(test_idx)}")
""")

# ---------------------------------------------------------------- Q1
md(r"""
## Q1. 프로모션 효과는 정말 고객마다 다른가?

타겟팅이 의미가 있으려면, 먼저 **처치 효과가 고객마다 다르다**는 신호가 있어야 합니다. 네 가지 처치 조합($A \in \{0,1,2,3\}$)에 대해 데이터 구조를 점검합니다.

1. 처치별 표본 수 — 각 처치에 충분한 관측치가 있는가?
2. 처치별 고객 특성 평균 — 어떤 고객군이 특정 처치를 받는 경향이 있는가?
3. 처치별 Revenue 분포 — 규모·분산·이상치가 처치마다 어떻게 다른가?
""")

code(r"""
treatment_counts = policy_df['treatment_name'].value_counts().reindex(TREATMENT_LABELS).rename_axis('treatment').to_frame('count')
treatment_counts['share'] = treatment_counts['count'] / len(policy_df)

display(treatment_counts)
""")

md(r"""
표본 수는 `none` 517명, `tech_support_only` 462명, `discount_only` 477명, `discount_plus_support` 544명입니다. 각 처치 비중이 23~27%로 비교적 고르게 분포해, 특정 처치에 표본이 극단적으로 부족한 문제는 없습니다. 네 가지 처치를 비교하는 정책학습을 진행하기에 안정적인 분포입니다.
""")

code(r"""
treatment_covariate_means = (
    policy_df
    .groupby('treatment_name')[covariates]
    .mean()
    .reindex(TREATMENT_LABELS)
)

plt.figure(figsize=(10, 5))
sns.heatmap(treatment_covariate_means.T, annot=True, fmt='.2f', cmap='YlGnBu', cbar_kws={'label': 'Mean'})
plt.xlabel('Treatments')
plt.ylabel('Covariate')
plt.title('Mean customer characteristics by treatments')
plt.tight_layout()
plt.savefig(FIGDIR / 'fig02_covariate_means.png', **SAVE_KW)
plt.show()
""")

md(r"""
처치별 고객 특성은 동일하지 않습니다. 특히 `Size`와 `IT Spend`의 평균이 처치 그룹별로 다르고, `discount_plus_support` 그룹에 큰 고객이 더 많이 포함되어 있습니다. 도메인적으로도 고객 규모나 IT 지출 수준에 따라 필요한 지원 형태가 달라질 수 있습니다.

이런 차이는 **처치 효과가 고객 특성에 따라 달라질 가능성**을 시사합니다. 동시에 처치 배정이 고객 특성과 얽혀 있다는 뜻이므로, 이후 정책 학습·평가는 이 차이를 보정할 수 있는 **AIPW**를 사용합니다.
""")

code(r"""
treatment_revenue = (
    policy_df
    .groupby(['treatment', 'treatment_name'])[outcome]
    .agg(['count', 'mean', 'median', 'std', 'min', 'max'])
    .reset_index()
)
display(treatment_revenue)

plt.figure(figsize=(8, 4))

sns.histplot(
    data=policy_df,
    x=outcome,
    hue='treatment_name',
    bins=40,
    element='step',
    stat='density',
    common_norm=False
)

plt.title('Revenue density by treatment')
plt.tight_layout()
plt.savefig(FIGDIR / 'fig03_revenue_dist.png', **SAVE_KW)
plt.show()
""")

md(r"""
Revenue 평균은 `none` 약 6,586, `discount_only` 약 12,248, `tech_support_only` 약 15,104, `discount_plus_support` 약 26,784입니다.

다만 규모가 큰 고객일수록 더 강한 개입을 받는 경향이 있으므로, **이 평균 차이를 그대로 처치 효과로 해석하면 안 됩니다.** Revenue 차이에는 고객 특성의 영향과 실제 처치 효과가 함께 섞여 있습니다. 이 교란을 어떻게 분리할 것인가가 바로 Q2의 주제입니다.

> **Q1 요약.** 처치 그룹 간 고객 특성과 결과 분포가 뚜렷이 다릅니다. 이는 (a) 처치 효과가 고객마다 다를 가능성과 (b) 처치 배정이 고객 특성에 의해 교란되어 있음을 동시에 시사합니다. 따라서 단순 평균 비교가 아니라 교란을 보정하는 인과적 접근이 필요합니다.
""")

# ---------------------------------------------------------------- Q2
md(r"""
## Q2. 관찰 데이터로 인과 효과를 신뢰할 수 있는가?

관찰 데이터에서 AIPW 추정이 인과적으로 유효하려면 두 가지 가정이 필요합니다.

**1. Unconfoundedness (비교란성)**

$$\{Y_i(0), Y_i(1), Y_i(2), Y_i(3)\} \perp A_i \mid X_i$$

관측된 공변량 $X_i$를 조건부로 했을 때, 처치 배정이 잠재 결과와 독립이어야 합니다. 즉, 고객 규모·IT 지출·직원 수 등이 처치 배정을 충분히 설명한다고 가정합니다.

**2. Positivity (양수성)**

$$P(A_i = a \mid X_i = x) > 0 \quad \forall a \in \{0,1,2,3\},\ \forall x$$

모든 고객 특성 범위에서 각 처치가 어느 정도 관측되어야 합니다.

이 중 Positivity는 propensity score를 추정해 직접 확인할 수 있습니다.

$$e_a(x) = P(A_i = a \mid X_i = x)$$

추가로 propensity score가 극단적으로 치우쳐 있지 않은지도 확인합니다. 특정 고객군에서 어떤 처치의 $e_a(x)$가 0에 매우 가까우면, 일부 관측치에 지나치게 큰 가중치가 부여되어 추정이 불안정해질 수 있습니다.
""")

code(r"""
multi_propensity = RandomForestClassifier(
    n_estimators=400,
    min_samples_leaf=20,
    random_state=SEED,
    n_jobs=1,
)
multi_propensity.fit(X_train, A_train)
e_hat_raw = multi_propensity.predict_proba(X_test)

propensity_summary = pd.DataFrame({
    'treatment': TREATMENT_LABELS,
    'mean_propensity': e_hat_raw.mean(axis=0),
    'min_propensity': e_hat_raw.min(axis=0),
    'p01_propensity': np.quantile(e_hat_raw, 0.01, axis=0),
    'propensity_below_0_05_rate': (e_hat_raw < 0.05).mean(axis=0),
})
display(propensity_summary)
""")

code(r"""
prop_df = pd.DataFrame(e_hat_raw, columns=TREATMENT_LABELS)
prop_long = prop_df.melt(var_name='treatment', value_name='propensity')

fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(
    data=prop_long, x='propensity', hue='treatment',
    bins=30, element='step', stat='density', common_norm=False, ax=ax,
)

ax.axvline(0.05, color='tomato', lw=1.5, ls='--', alpha=0.8, label='threshold = 0.05')
ax.legend(title='Treatment', fontsize=8)
ax.set_xlabel('Propensity score')
ax.set_ylabel('Density')
ax.set_title('Propensity score distribution by treatment')
plt.tight_layout()
plt.savefig(FIGDIR / 'fig04_propensity.png', **SAVE_KW)
plt.show()
""")

md(r"""
이 데이터에서 $\hat e_a(X_i)$의 최솟값은 약 **0.058**이며, `e_hat < 0.05`인 경우도 관측되지 않았습니다. 즉, 극단적으로 작은 propensity score로 일부 관측치에 과도한 가중치가 부여되는 문제는 크지 않습니다. 그래프에서도 네 처치의 propensity 분포가 전반적으로 잘 겹쳐, 뚜렷한 positivity 위반은 보이지 않습니다.

> **Q2 요약.** Positivity는 데이터로 확인되어 충족됩니다. Unconfoundedness는 검정 불가능한 가정이지만, 고객 규모·직원 수·IT 지출 등 처치 배정을 설명할 핵심 변수들이 관측되어 있어 합리적인 가정으로 받아들입니다. 따라서 이후 분석은 outcome model과 propensity model을 함께 쓰는 **doubly robust(AIPW)** 추정을 채택합니다.
""")

# ---------------------------------------------------------------- Q3
md(r"""
## Q3. 누구에게 무엇을 배정해야 하는가?

이제 본격적으로 정책을 학습합니다. 세 가지 방법을 비교합니다.

- **Plug-in Policy (DRLearner):** 고객별 CATE를 추정한 뒤 기대 순이익이 가장 큰 처치를 선택. 유연하지만 CATE 추정 품질에 민감.
- **DRPolicyTree:** AIPW score를 직접 최대화하되 정책을 얕은 의사결정 트리로 제한 → **해석 가능**.
- **DRPolicyForest:** AIPW score를 직접 최대화하되 forest를 사용 → 분산이 작고 안정적이지만 해석은 어려움.

세 정책 모두 train set에서 학습하고, 동일한 test set에서 가치를 비교합니다(Q4).
""")

# ------ Plug-in
md(r"""
### Q3.1. Plug-in Policy

Plug-in policy는 먼저 고객별 처치 효과(CATE)를 추정한 뒤 그 값으로 정책을 만듭니다. 여러 처치가 있으므로 `none`을 baseline으로 두고 `DRLearner`로 상대효과를 추정합니다.

$$\hat\tau_a(x) = \widehat{\mathbb{E}}[Y^{net}(a) - Y^{net}(0) \mid X=x], \qquad a \in \{1,2,3\}$$

baseline의 상대효과는 0이므로 고객별로 $[0, \hat\tau_1(x), \hat\tau_2(x), \hat\tau_3(x)]$를 비교해 가장 큰 처치를 선택합니다.

$$\hat\pi_{plugin}(x) = \arg\max_{a \in \{0,1,2,3\}} \widehat{\mathbb{E}}[Y^{net}(a) - Y^{net}(0) \mid X=x]$$

> **NOTE.** "각 고객의 AIPW score $\hat\Gamma_{i,a}$ 중 가장 큰 처치를 고르면 되지 않나?"라고 생각할 수 있습니다. 그러나 AIPW score는 개별 관측치 수준에서 분산이 매우 커서, pointwise argmax 정책은 노이즈에 과적합됩니다. AIPW score는 반드시 **집계된 형태**로 사용해야 합니다(정책 가치 추정, 노드 단위 평균 최적화, pseudo-outcome 회귀 등).
""")

code(r"""
dr_cate = DRLearner(
    model_regression=RandomForestRegressor(
        n_estimators=400,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    ),
    model_propensity=RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    ),
    model_final=RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    ),
    categories=[0, 1, 2, 3],
    min_propensity=0.02,
    cv=3,
    random_state=SEED,
)
dr_cate.fit(Y_net_train, A_train, X=X_train)

# none을 baseline으로, 나머지 처치별 E[Y_net(a) - Y_net(0) | X] 반환
cate_vs_none = dr_cate.const_marginal_effect(X_test)
plugin_treatment_values = np.column_stack([
    np.zeros(len(X_test)),  # none: baseline, 상대효과 = 0
    cate_vs_none,
])
pi_plugin = np.argmax(plugin_treatment_values, axis=1)
""")

code(r"""
pd.Series(pi_plugin).map(TREATMENT_NAMES).value_counts(normalize=True).reindex(TREATMENT_LABELS).fillna(0)
""")

code(r"""
none_idx = np.where(pi_plugin == 0)[0][:3]
tech_idx = np.where(pi_plugin == 1)[0][:3]
both_idx = np.where(pi_plugin == 3)[0][:3]
sample_ids = np.concatenate([none_idx, tech_idx, both_idx])

df_plugin_sample = pd.DataFrame(X_test[sample_ids], columns=covariates)[['Size', 'Employee Count', 'IT Spend']]
df_plugin_sample['assigned_treatment'] = pd.Series(pi_plugin[sample_ids]).map(TREATMENT_NAMES).values
df_plugin_sample[['tau_tech', 'tau_disc', 'tau_both']] = np.round(cate_vs_none[sample_ids], 0).astype(int)
df_plugin_sample.index = pd.RangeIndex(len(df_plugin_sample))
df_plugin_sample
""")

md(r"""
plug-in 정책은 약 50%에게 `tech_support_only`, 37%에게 `discount_plus_support`, 약 9%에게 `none`을 배정합니다. 비용을 함께 고려하면서, 기대 순이익이 음수로 예상되는 일부 고객에게는 처치를 하지 않는 선택이 나타납니다.
""")

# ------ Tree
md(r"""
### Q3.2. Policy Tree

현업에서는 성능뿐 아니라 **정책의 설명 가능성**도 중요합니다. 얕은 의사결정 트리 기반 정책이 실무에서 자주 쓰이는 이유는 다음과 같습니다.

- **이해관계자 설명:** 직관적인 분기 규칙이라 정책을 쉽게 설명·공유할 수 있습니다.
- **공정성 검토:** 어떤 고객이 어떤 처치를 받는지 구조가 명확해 편향 점검이 쉽습니다.
- **운영 안정성:** 단순한 규칙 기반 정책이 운영·관리 측면에서 안정적입니다.

이 경우 정책을 모든 가능한 함수에서 찾는 대신, 제한된 정책 클래스 $\Pi$ 안에서 탐색합니다.

$$\hat\pi = \arg\max_{\pi \in \Pi} \frac{1}{n}\sum_{i=1}^{n} \widehat\Gamma_{i,\pi(X_i)}$$

`econml`의 `DRPolicyTree`를 사용하며, leaf가 지나치게 작아지면 다중 처치 환경에서 value 추정이 불안정해지므로 `min_samples_leaf`로 이를 방지합니다.
""")

code(r"""
dr_policy_tree = DRPolicyTree(
    max_depth=2,
    min_samples_leaf=30,
    model_regression=RandomForestRegressor(
        n_estimators=400,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    ),
    model_propensity=RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    ),
    categories=[0, 1, 2, 3],
    min_propensity=0.02,
    cv=3,
    random_state=SEED,
)
dr_policy_tree.fit(Y_net_train, A_train, X=X_train)
pi_tree = dr_policy_tree.predict(X_test).astype(int).ravel()

pd.Series(pi_tree).map(TREATMENT_NAMES).value_counts(normalize=True).reindex(TREATMENT_LABELS).fillna(0)
""")

code(r"""
fig, ax = plt.subplots(figsize=(13, 7))
dr_policy_tree.plot(feature_names=covariates, treatment_names=TREATMENT_LABELS, ax=ax)
ax.set_title('4-way DRPolicyTree')
plt.tight_layout()
plt.savefig(FIGDIR / 'fig05_policy_tree.png', **SAVE_KW)
plt.show()
""")

md(r"""
이 트리 정책은 주로 `Size`를 기준으로 고객을 나눕니다. 약 20%의 고객에게는 `none`을 배정하는데, 비용을 반영한 결과 일부 고객은 처치 시 기대 순이익이 낮아 처치하지 않는 편이 낫다고 판단한 것입니다. 전체적으로 규모가 큰 고객에게 `discount_plus_support`를, 그 외에는 주로 `tech_support_only`를 배정합니다.
""")

# ------ Forest
md(r"""
### Q3.3. Policy Forest

Policy Forest 역시 AIPW score를 직접 최대화하지만, 단일 tree 대신 여러 tree의 결과를 평균해 **분산이 작고** 복잡한 이질성을 더 안정적으로 학습합니다. 대신 하나의 명확한 의사결정 규칙으로 해석하기는 어렵습니다. `econml`의 `DRPolicyForest`를 사용합니다.
""")

code(r"""
dr_policy_forest = DRPolicyForest(
    n_estimators=400,
    max_depth=5,
    min_samples_leaf=30,
    model_regression=RandomForestRegressor(
        n_estimators=400,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    ),
    model_propensity=RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    ),
    categories=[0, 1, 2, 3],
    min_propensity=0.02,
    cv=3,
    random_state=SEED,
    n_jobs=1,
)
dr_policy_forest.fit(Y_net_train, A_train, X=X_train)
pi_forest = dr_policy_forest.predict(X_test).astype(int).ravel()

pd.Series(pi_forest).map(TREATMENT_NAMES).value_counts(normalize=True).reindex(TREATMENT_LABELS).fillna(0)
""")

md(r"""
DRPolicyForest는 전반적으로 plug-in 정책과 유사한 배정을 보입니다. `none` 11%, `tech_support_only` 47%, `discount_plus_support` 42%로, plug-in보다 `discount_plus_support` 비중이 조금 더 높습니다.
""")

# ------ Feature importance
md(r"""
### Q3.4. 어떤 고객 특성이 배정을 좌우하는가?

DRPolicyForest는 단일 트리 구조가 없어 분기 규칙으로 직접 해석하기 어렵지만, `feature_importances_`로 **어떤 고객 특성이 처치 배정을 주도하는지** 파악할 수 있습니다. 이 값은 각 특성이 forest의 분기 과정에서 정책 이질성(policy heterogeneity)을 얼마나 유발하는지를 정규화한 점수입니다. 완전한 인과적 해석보다는 탐색적 지표로 활용합니다.
""")

code(r"""
importances = dr_policy_forest.feature_importances_
fi_df = pd.DataFrame({
    'feature': covariates,
    'importance': importances,
}).sort_values('importance', ascending=False).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(7, 4))
sns.barplot(data=fi_df, x='importance', y='feature', ax=ax, color='steelblue')
ax.set_title('DRPolicyForest - Feature Importances')
ax.set_xlabel('Importance (normalized)')
ax.set_ylabel('')
plt.tight_layout()
plt.savefig(FIGDIR / 'fig06_feature_importance.png', **SAVE_KW)
plt.show()

display(fi_df)
""")

md(r"""
`Employee Count`(42%)와 `Size`(38%)가 전체 중요도의 약 80%를 차지하며, **고객 규모와 직원 수가 처치 배정을 주도하는 핵심 요인**임을 확인할 수 있습니다. `PC Count`(13%)와 `IT Spend`(8%)도 일부 기여하지만, Flag 변수들은 거의 영향을 미치지 않습니다. 이는 DRPolicyTree가 `Size`를 기준으로 분기했던 결과와도 일치합니다.

> **Q3 요약.** 세 정책 모두 "규모가 큰 고객 → 기술지원+할인, 그 외 → 주로 기술지원, 기대 순이익이 낮은 일부 → 무처치"라는 일관된 배정 패턴을 학습했습니다. 배정의 핵심 신호는 직원 수와 고객 규모입니다.
""")

# ---------------------------------------------------------------- Q4
md(r"""
## Q4. 학습한 정책이 정말 더 나은가?

이제 학습한 정책들을 동일한 test set의 **AIPW score** 기준으로 비교합니다. 비교를 위해 모든 고객에게 동일한 처치를 적용하는 baseline 정책(`all_none`, `all_tech_support_only`, `all_discount_only`, `all_discount_plus_support`)도 함께 평가합니다.

학습된 정책의 value가 가장 좋은 baseline보다 높다면, **모두에게 동일한 처치를 적용하는 것보다 고객별 타겟팅이 더 효과적**이라는 의미입니다.

AIPW(Augmented Inverse Probability Weighting) score는 다음과 같이 정의합니다.

$$\hat\Gamma_{i,a} = \hat\mu_a(X_i) + \frac{\mathbf{1}[A_i=a]}{\hat e_a(X_i)}\bigl(Y_i^{net} - \hat\mu_a(X_i)\bigr)$$

- $\hat\mu_a(X_i)$: outcome model이 예측한 $E[Y^{net}(a)\mid X_i]$
- $\hat e_a(X_i)$: propensity model이 예측한 $P(A_i=a\mid X_i)$
- 두 번째 항: 실제 관측값과 예측값의 차이를 IPW로 보정

이 구조 덕분에 outcome model과 propensity model 중 **하나만 올바르게 추정되어도** 불편성이 유지됩니다. 이를 doubly robust(이중 견고성)라고 부릅니다.
""")

code(r"""
Y_net_train = Y_net[train_idx]
Y_net_test  = Y_net[test_idx]

e_hat_net = np.clip(e_hat_raw, 0.02, 0.98)
e_hat_net = e_hat_net / e_hat_net.sum(axis=1, keepdims=True)

gamma_net = np.zeros((len(X_test), 4))
mu_hat_net = np.zeros((len(X_test), 4))

for treatment_id in range(4):
    outcome_model = RandomForestRegressor(
        n_estimators=400,
        min_samples_leaf=20,
        random_state=SEED,
        n_jobs=1,
    )
    outcome_model.fit(X_train[A_train == treatment_id], Y_net_train[A_train == treatment_id])
    mu_a = outcome_model.predict(X_test)
    observed_a = (A_test == treatment_id).astype(float)

    gamma_net[:, treatment_id] = mu_a + observed_a / e_hat_net[:, treatment_id] * (Y_net_test - mu_a)
    mu_hat_net[:, treatment_id] = mu_a
""")

code(r"""
sample_ids = np.arange(5)

sample_prediction_table = pd.concat(
    {
        'sample': pd.DataFrame({
            'sample_id': sample_ids,
            'actual_treatment': pd.Series(A_test[sample_ids]).map(TREATMENT_NAMES).to_numpy(),
            'observed_net_outcome': Y_net_test[sample_ids],
        }),
        'e_hat': pd.DataFrame(e_hat_net[sample_ids], columns=TREATMENT_LABELS),
        'mu_hat': pd.DataFrame(mu_hat_net[sample_ids], columns=TREATMENT_LABELS),
        'gamma': pd.DataFrame(gamma_net[sample_ids], columns=TREATMENT_LABELS),
    },
    axis=1,
)

sample_prediction_table
""")

code(r"""
policy_assignments = {
    **{f'all_{treatment_name}': np.full(len(X_test), treatment_id) for treatment_id, treatment_name in TREATMENT_NAMES.items()},
    'plugin_drlearner_4treatment': pi_plugin,
    'dr_policy_tree_4treatment': pi_tree,
    'dr_policy_forest_4treatment': pi_forest,
}

eval_rows = []
for policy_name, policy_assignment in policy_assignments.items():
    pi = np.asarray(policy_assignment).astype(int).ravel()
    scores = gamma_net[np.arange(len(pi)), pi]

    row = {
        'policy': policy_name,
        'value': scores.mean(),
        'value_se': scores.std(ddof=1) / np.sqrt(len(scores)),
    }
    for treatment_id, treatment_name in TREATMENT_NAMES.items():
        row[f'rate_{treatment_name}'] = np.mean(pi == treatment_id)
    eval_rows.append(row)

policy_eval = pd.DataFrame(eval_rows)
policy_eval['ci_lower'] = policy_eval['value'] - 1.96 * policy_eval['value_se']
policy_eval['ci_upper'] = policy_eval['value'] + 1.96 * policy_eval['value_se']

display_cols = ['policy', 'value', 'ci_lower', 'ci_upper'] + [f'rate_{n}' for n in TREATMENT_LABELS]
policy_eval.sort_values('value', ascending=False)[display_cols]
""")

code(r"""
fig, axes = plt.subplots(1, 2, figsize=(15, 5))
plot_df = policy_eval.sort_values('value', ascending=False)
sns.barplot(data=plot_df, x='value', y='policy', ax=axes[0], color='seagreen')
axes[0].set_title('4-way net policy value')
axes[0].set_xlabel('AIPW-estimated net value')
axes[0].set_ylabel('')

treatment_rate_cols = [f'rate_{name}' for name in TREATMENT_LABELS]
rate_df = policy_eval.set_index('policy')[treatment_rate_cols]
rate_df.columns = TREATMENT_LABELS
rate_df.loc[['plugin_drlearner_4treatment', 'dr_policy_tree_4treatment', 'dr_policy_forest_4treatment']].plot(kind='barh', stacked=True, ax=axes[1], colormap='tab20')
axes[1].set_title('Assigned treatment share')
axes[1].set_xlabel('Share')
axes[1].set_ylabel('')
axes[1].legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
plt.tight_layout()
plt.savefig(FIGDIR / 'fig07_policy_value.png', **SAVE_KW)
plt.show()
""")

md(r"""
세 학습 정책 모두 단일 처치 정책보다 높은 가치를 가집니다. **고객별로 처치를 다르게 배정하는 것이 모두에게 같은 처치를 적용하는 것보다 효과적**이라는 의미입니다.

- 학습 정책: DRLearner plug-in(**11,798**) > DRPolicyForest(11,619) > DRPolicyTree(11,149)
- 단일 처치: `all_tech_support_only`(10,527) > `all_discount_plus_support`(10,137) > `all_discount_only`(7,545) > `all_none`(7,249)

plug-in과 forest는 신뢰구간이 상당 부분 겹쳐 실질적 차이가 있다고 보기는 어렵습니다. 이론적으로는 AIPW score를 직접 최적화하는 DR 정책이 유리할 수 있지만, 실제로는 표본 크기·데이터 특성에 따라 결과가 달라집니다. tree 정책은 해석 가능한 구조를 유지하는 대신 성능을 일부 양보했습니다. `all_discount_plus_support`가 `all_tech_support_only`보다 낮은 이유는, 할인 비용이 고객 규모에 따라 커지도록 설정해 일부 고객에서 할인의 순수익이 비용을 상쇄하지 못했기 때문입니다.

> **Q4 요약.** 세 학습 정책 모두 최선의 단일 처치 정책보다 높은 순이익을 냅니다(plug-in 기준 +12%, 무처치 대비 +63%). 타겟팅의 가치가 데이터로 확인됩니다.
""")

# ---------------------------------------------------------------- Q5
md(r"""
## Q5. 예산이 제한되면 어떤 정책이 유리한가?

지금까지는 어떤 정책이 전체적으로 더 높은 AIPW value를 갖는지 비교했습니다. 그러나 실제로는 예산이 제한되어 있을 수 있습니다. 같은 예산 안에서 어떤 정책이 더 효율적인지 비교하려면 **비용 곡선(cost curve)**이 유용합니다.

먼저 고객별 기대 비용 $E[C(a) \mid X_i]$를 추정합니다. 실제 비용은 해당 고객이 받은 처치에서만 관측되므로, 처치별로 훈련 데이터에서 비용 회귀 모델을 학습해 test set에 적용합니다.
""")

code(r"""
# 처치별 E[C(a) | X] 추정
# c_hat_test[i, a] = 고객 i가 처치 a를 받을 때의 예측 비용
c_true_by_treatment = {1: c_tech, 2: c_disc, 3: c_tech + c_disc}

c_hat_test = np.zeros((len(X_test), 4))   # 처치 0 → 비용 = 0
for treatment_id in [1, 2, 3]:
    mask_train = (A_train == treatment_id)
    mdl = RandomForestRegressor(n_estimators=300, min_samples_leaf=20,
                                random_state=SEED, n_jobs=1)
    mdl.fit(X_train[mask_train], c_true_by_treatment[treatment_id][train_idx[mask_train]])
    c_hat_test[:, treatment_id] = np.maximum(mdl.predict(X_test), 200.0)

print("Estimated E[C(a)|X] - test set (mean +/- std):")
for treatment_id, treatment_name in TREATMENT_NAMES.items():
    if treatment_id > 0:
        print(f"  {treatment_name:25s}: {c_hat_test[:, treatment_id].mean():8,.0f} +/- {c_hat_test[:, treatment_id].std():6,.0f}")
""")

md(r"""
비용 곡선의 두 축은 다음과 같습니다.

- **x축:** 고객 1인당 누적 평균 처치 비용
- **y축:** 고객 1인당 누적 평균 순수익 — baseline(`none`) 대비 증분이며 **비용이 이미 차감된 값**

각 정책에서 순수익/비용 비율 $\hat\rho(x) = \hat\tau(x) / \hat\gamma(x)$이 높은 고객부터 순서대로 처치합니다. $x = B$에서 세로선을 그으면 예산 $B$ 하의 정책 비교가 됩니다. 같은 예산에서 y값이 높을수록 더 효율적인 정책입니다. 곡선의 종점(●)은 처치 대상 전원을 처치했을 때의 위치입니다.
""")

code(r"""
def policy_cost_curve(pi_eval, gamma_matrix, c_hat_matrix):
    '''
    처치별 고객 비용 추정값을 사용해 비용 곡선을 생성합니다.
    c_hat_matrix[i, a] = E[C(a) | X_i]

    x = 고객 1인당 누적 평균 처치 비용 (gross)
    y = 고객 1인당 누적 평균 순이익 (Y_net에 비용이 이미 차감된 값)

    처치 고객은 순이익 / 추정 비용 비율(내림차순)로 정렬합니다.
    '''
    pi = np.asarray(pi_eval).ravel().astype(int)
    n = len(pi)
    treated = pi > 0
    if treated.sum() == 0:
        return np.array([0.0]), np.array([0.0])

    benefit = gamma_matrix[np.arange(n), pi] - gamma_matrix[:, 0]
    cost    = c_hat_matrix[np.arange(n), pi].astype(float)

    b_t, c_t = benefit[treated], cost[treated]
    ratio = np.where(c_t > 0, b_t / c_t, b_t)
    order = np.argsort(-ratio)

    cum_cost    = np.r_[0, np.cumsum(c_t[order])]
    cum_benefit = np.r_[0, np.cumsum(b_t[order])]
    return cum_cost / n, cum_benefit / n


n_test = len(X_test)
policies_curve = [
    ('DRLearner plug-in',         pi_plugin),
    ('DRPolicyTree (depth=2)',     pi_tree),
    ('DRPolicyForest',            pi_forest),
    ('all_discount_plus_support', np.full(n_test, 3)),
    ('all_tech_support_only',     np.full(n_test, 1)),
]

fig, ax = plt.subplots(figsize=(8, 6))
colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']

for (name, pi_eval), color in zip(policies_curve, colors):
    cc, cg = policy_cost_curve(pi_eval, gamma_net, c_hat_test)
    ax.plot(cc, cg, lw=2, color=color,
            label=f'{name}  (cost={cc[-1]:,.0f}, net benefit={cg[-1]:,.0f})')
    ax.scatter([cc[-1]], [cg[-1]], s=50, color=color, zorder=5)

budget_example = 5_000
ax.axvline(budget_example, color='gray', lw=1.5, ls='--', alpha=0.7,
           label=f'Budget = ${budget_example:,}/customer')

ax.set_xlabel('Avg cumulative cost per customer ($)', fontsize=11)
ax.set_ylabel('Avg cumulative net benefit per customer ($)', fontsize=11)
ax.set_title('Policy cost curves - cut at x=B for budget-constrained comparison', fontsize=11)
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(FIGDIR / 'fig08_cost_curve.png', **SAVE_KW)
plt.show()
""")

md(r"""
**예산 규모에 따라 효율적인 정책이 다릅니다.**

- **소액 예산(\$1,000~3,000):** `all_tech_support_only`가 가장 효율적입니다. 기술지원 평균 비용이 낮아, 적은 예산으로도 순수익/비용 비율이 높은 고객부터 빠르게 처치할 수 있기 때문입니다.
- **중간 예산(\$4,000~6,000):** 학습 정책(plug-in, forest)이 앞섭니다. 고객별 최적 처치 배정 효과가 발휘되어 같은 비용으로 더 높은 순이익을 냅니다.
- **예산 전부 소진:** 학습 정책이 가장 효율적입니다. plug-in은 약 \$6,600을 써서 \$4,561, forest는 약 \$6,900을 써서 \$4,376의 순이익을 냅니다. 반면 `all_discount_plus_support`는 \$10,700을 전부 소진해도 순이익이 \$2,887에 그쳐 예산 대비 효율이 가장 낮습니다.

> **Q5 요약.** "어떤 정책이 최선인가"는 예산에 의존합니다. 예산이 매우 적으면 저비용 단일 처치가, 예산이 충분하면 타겟팅 정책이 유리합니다. 비용 곡선은 예산 의사결정에 직접 활용할 수 있는 도구입니다.
""")

# ---------------------------------------------------------------- 결론
md(r"""
## 결론 및 권고

**분석 요약.** 약 2,000명의 관찰 데이터에서, 비용을 반영한 순이익을 기준으로 4가지 프로모션의 고객별 최적 배정을 학습했습니다. 처치 효과의 이질성을 진단(Q1)하고 인과 식별 가정을 점검(Q2)한 뒤, 세 가지 정책을 학습(Q3)하고 학습/평가 데이터를 분리해 doubly robust(AIPW) 기준으로 가치를 비교(Q4)했으며, 예산 제약 하의 효율(Q5)까지 평가했습니다.

**비즈니스 권고.**

1. **모두에게 동일한 프로모션을 주지 말고, 타겟팅하라.** 고객별 타겟팅은 최선의 단일 처치 대비 약 12%, 무처치 대비 약 63% 높은 순이익을 냅니다.
2. **배정 기준은 고객 규모와 직원 수다.** 규모가 큰 고객에게는 *기술지원+할인*, 그 외 고객에게는 주로 *기술지원*을, 기대 순이익이 낮은 일부에게는 *무처치*를 권합니다.
3. **예산에 맞춰 정책을 선택하라.** 예산이 빠듯하면 저비용 *전원 기술지원*이 효율적이고, 예산이 1인당 \$4,000을 넘어가면 학습 정책으로 전환하는 것이 유리합니다.
4. **운영 환경에 맞는 모델을 골라라.** 성능 최우선이면 plug-in/forest를, 이해관계자 설명·공정성 검토·운영 안정성이 중요하면 약간의 성능을 양보하더라도 해석 가능한 **depth=2 트리 정책**을 권합니다.

**한계와 다음 단계.**

- 비용은 실제 데이터가 아니라 **시뮬레이션** 값입니다. 실제 비용 데이터가 확보되면 결론이 달라질 수 있습니다.
- Unconfoundedness는 검정 불가능한 가정입니다. 가능하다면 소규모 **무작위 실험(RCT)**으로 학습된 정책을 검증하는 것이 이상적입니다.
- 표본이 약 1,000명(test) 수준이라 정책 간 차이의 신뢰구간이 겹칩니다. 표본을 늘리면 정책 선택의 확신도가 높아집니다.
- 다음 단계로 정책 가치의 신뢰구간 추정(예: 정책 가치에 대한 부트스트랩), 시간에 따른 정책 모니터링, A/B 테스트 기반 검증을 제안합니다.
""")

# ---------------------------------------------------------------- 참고
md(r"""
## 참고 자료

이 분석은 Athey & Wager (2021)와 Stanford ML+CI Tutorial을 주요 참고 자료로 작성되었습니다.

- **Athey, S., & Wager, S. (2021).** Policy Learning with Observational Data. *Econometrica.* [arxiv.org/abs/1702.02896](https://arxiv.org/abs/1702.02896)
- **Sun, L., Du, X., Wager, S., et al. (2021).** Treatment Allocation under Uncertain Costs. [arxiv.org/abs/2103.11066](https://arxiv.org/abs/2103.11066)
- **Imai, K., & Li, M. L. (2019).** Experimental Evaluation of Individualized Treatment Rules. [arxiv.org/pdf/1905.05389.pdf](https://arxiv.org/pdf/1905.05389.pdf)
- **Stanford ML+CI Tutorial — Policy Learning I (Binary Treatment).** [bookdown.org/.../policy-learning-i---binary-treatment.html](https://bookdown.org/stanfordgsbsilab/ml-ci-tutorial/policy-learning-i---binary-treatment.html)
""")

# ---------------------------------------------------------------- assemble
nb['cells'] = cells
nb['metadata'] = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
}
nbf.write(nb, 'who_should_be_treated_ko.ipynb')
print(f'wrote notebook with {len(cells)} cells')
