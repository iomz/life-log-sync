# Metrics

## Activity Level

Activity level uses explicit workouts plus estimated unlogged steps from the
Withings daily step total.

- None: no workouts and no unlogged steps
- Light: <=5 km and <=60 min
- Moderate: <=12 km and <=120 min
- High: more than 12 km or 120 min

## Activity Score

Activity Score uses non-swimming distance plus duration:

`score = distance_km + duration_min / 12`

When Withings daily steps are available, ingest subtracts steps already covered
by logged walk/run workouts before adding step effort. Logged walk/run steps come
from workout step counts when present; otherwise they are estimated from distance
(1300 steps/km walking, 1200 steps/km running). Remaining daily steps are treated
as walking-equivalent effort (1300 steps/km, 12 min/km). This keeps total daily
steps represented while avoiding double-counting explicit walk/run workouts.

## Recovery Compatibility

- Good: None or Light
- Acceptable: Moderate
- Poor: High

## Walking Trend

Compare current 7-day average daily walking distance with the previous 7-day
average.

- Threshold: 0.50 km/day
- Increasing: current average is at least 0.50 km/day higher
- Stable: difference is within +/-0.50 km/day
- Decreasing: current average is at least 0.50 km/day lower
- Unknown: insufficient data

## Weight Trend

Compare current 7-day average weight with the previous 7-day average.

- Threshold: 0.30 kg
- Increasing: current average is at least 0.30 kg higher
- Stable: difference is within +/-0.30 kg
- Decreasing: current average is at least 0.30 kg lower
- Unknown: insufficient data

## Data Coverage

Data coverage describes the Withings activity records used for the generated context.

- Sources: source names present.
- Activities: count of activities for the target date.
