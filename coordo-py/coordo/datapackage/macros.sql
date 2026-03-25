CREATE OR REPLACE MACRO gini(col) AS (
    SELECT
        (
            2 * list_sum(
                list_transform(
                    range(1, len(sorted) + 1),
                    (i) -> i * sorted[i]
                )
            ) / (len(sorted) * list_sum(sorted))
            - ((len(sorted) + 1) / len(sorted))
        )
    FROM (
        SELECT list_sort(list(col)) AS sorted
    )
);

CREATE OR REPLACE MACRO categorical_gini(col) AS (
    (
        SELECT SUM((cnt/total)^2)
        FROM (
            SELECT
                x,
                COUNT(*) AS cnt,
                SUM(COUNT(*)) OVER () AS total
            FROM unnest(list(col)) AS x
            GROUP BY x
        )
    )
);
