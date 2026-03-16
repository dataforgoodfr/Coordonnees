CREATE OR REPLACE MACRO gini(col) AS (
  (
    (2 * list_sum(
        list_transform(
            range(1, len(col) + 1),
            (x, i) -> x * list_sort(col)[i]
        )
    ) / (len(col) * list_sum(col)))
    - ((len(col) + 1) / len(col))
  )
);
