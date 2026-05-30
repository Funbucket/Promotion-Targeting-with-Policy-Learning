# Promotion Targeting with Policy Learning

**Budget-constrained treatment allocation using causal policy learning**

> 제한된 예산 안에서 누구에게 어떤 프로모션을 제공해야 전체 순이익이 가장 커질까?

한 소프트웨어 회사가 고객에게 *기술지원*과 *할인* 두 가지 프로모션을 제공할 수 있을 때(조합 시 4가지 처치), **관찰 데이터**를 활용해 고객별 최적 처치와 예산 제약 하의 순이익을 평가하는 프로젝트입니다.

분석은 다섯 가지 비즈니스 질문으로 구성됩니다.

1. **Q1.** 프로모션 효과는 정말 고객마다 다른가? (이질성 진단)
2. **Q2.** 관찰 데이터로 인과 효과를 신뢰할 수 있는가? (식별 가정)
3. **Q3.** 누구에게 무엇을 배정해야 하는가? (정책학습)
4. **Q4.** 학습한 정책이 정말 더 나은가? (정책 평가)
5. **Q5.** 예산이 제한되면 어떤 정책이 유리한가? (예산 제약)

## 핵심 결과

| 정책 | 고객사당 평균 순이익 | 처치 없음 대비 |
| --- | ---: | ---: |
| 처치 없음 (all none) | $7,249 | - |
| 최선의 단일 처치 (전원 기술지원) | $10,527 | +45% |
| **고객별 타겟팅 (DRLearner plug-in)** | **$11,798** | **+63%** |

- 고객별 타겟팅은 최선의 단일 처치 정책보다 약 **12%**, 처치 없음 대비 약 **63%** 높은 순이익.
- 처치 배정을 좌우하는 핵심 요인은 **직원 수(42%)와 고객 규모(38%)**.
- 예산 수준에 따라 최적 정책이 달라짐(소액 예산 -> 전원 기술지원, 중간 예산 이상 -> 학습 정책).

## 방법론

- **다중 처치(4-way) 정책학습**: DRLearner plug-in · `DRPolicyTree` · `DRPolicyForest` (`econml`)
- **Doubly Robust (AIPW) score**로 학습/평가 데이터를 분리해 정책 가치 추정
- 비용을 반영한 **순이익(net outcome)** 기준 최적화 + **비용 곡선**으로 예산 제약 분석

## 산출물

| 파일 | 설명 |
| --- | --- |
| `promotion_targeting_policy_learning_ko.ipynb` | 전체 분석 노트북 (코드 + 결과 + 해설) |
| `reports/promotion_targeting_policy_learning_whitepaper.pdf` | 코드를 숨긴 컨설팅 리포트 (한국어) |
| `reports/promotion_targeting_policy_learning_whitepaper.tex` | 리포트 LaTeX 소스 |
| `figures/` | 리포트에 사용된 그림 (노트북 실행 시 생성) |

## 폴더 구조

```text
Promotion-Targeting-with-Policy-Learning/
├── README.md
├── requirements.txt
├── promotion_targeting_policy_learning_ko.ipynb
├── data/
│   └── multi_attribution_sample.csv
├── reports/
│   ├── promotion_targeting_policy_learning_whitepaper.pdf
│   └── promotion_targeting_policy_learning_whitepaper.tex
├── figures/
│   ├── fig01_cost_dist.png
│   ├── fig02_covariate_means.png
│   ├── fig03_revenue_dist.png
│   ├── fig04_propensity.png
│   ├── fig05_policy_tree.png
│   ├── fig06_feature_importance.png
│   ├── fig07_policy_value.png
│   ├── fig08_cost_curve.png
│   └── fig09_cost_validation.png
└── assets/
    └── AJStyles&Undertaker.jpg
```

## 재현 방법

```bash
# 1) 가상환경 + 의존성
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) 노트북 실행 (figures/ 자동 생성)
jupyter nbconvert --to notebook --execute --inplace promotion_targeting_policy_learning_ko.ipynb

# 3) 리포트 PDF 컴파일 (XeLaTeX + kotex 필요)
cd reports && xelatex promotion_targeting_policy_learning_whitepaper.tex && xelatex promotion_targeting_policy_learning_whitepaper.tex
```

## 데이터

데이터는 Microsoft의 공개 샘플 `multi_attribution_sample.csv`를 사용했습니다.

https://microsoft.github.io/SynapseML/docs/Explore%20Algorithms/Causal%20Inference/Quickstart%20-%20Measure%20Causal%20Effects/

`data/multi_attribution_sample.csv` - 약 2,000곳의 고객 특성·개입·매출. 비용 정보는 고객 특성에 따라 시뮬레이션해 사용합니다.

## 참고 자료

- Athey, S., & Wager, S. (2021). *Policy Learning with Observational Data*. Econometrica. [arxiv.org/abs/1702.02896](https://arxiv.org/abs/1702.02896)
- Sun, L., Du, X., Wager, S., et al. (2021). *Treatment Allocation under Uncertain Costs*. [arxiv.org/abs/2103.11066](https://arxiv.org/abs/2103.11066)
- Imai, K., & Li, M. L. (2019). *Experimental Evaluation of Individualized Treatment Rules*. [arxiv.org/pdf/1905.05389.pdf](https://arxiv.org/pdf/1905.05389.pdf)

---

*Written by 조해창 · [GitHub](https://github.com/Funbucket) · [LinkedIn](https://www.linkedin.com/in/hae-chang-cho/)*
