CREATE OR REPLACE MACRO merge(col) AS st_union_agg(col);

CREATE OR REPLACE MACRO percentile(col, pct) AS quantile_cont(col, pct / 100);

CREATE OR REPLACE MACRO shannon(col) AS ln(2) * list_entropy(list(col));

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
                COUNT(*) AS cnt,
                SUM(COUNT(*)) OVER () AS total
            FROM unnest(list(col)) AS x
            GROUP BY x
        )
    )
);

CREATE OR REPLACE MACRO value_counts(col) AS list_reduce(list(col), lambda counts, x: struct_update(counts, x := coalesce(counts[x], 0) + 1));
