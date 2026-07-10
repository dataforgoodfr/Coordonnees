-- Copyright COORDONNÉES 2025, 2026
-- SPDX-License-Identifier: MPL-2.0

CREATE OR REPLACE MACRO gini_arr(arr) AS (
    2 * list_sum(
        list_transform(
            range(1, len(list_sort(arr)::DOUBLE[]) + 1),
            i -> i::BIGINT * (list_sort(arr)::DOUBLE[])[i]
        )
    ) / (len(list_sort(arr)::DOUBLE[]) * list_sum(list_sort(arr)::DOUBLE[]))
    - (len(list_sort(arr)::DOUBLE[]) + 1.0) / len(list_sort(arr)::DOUBLE[])
);