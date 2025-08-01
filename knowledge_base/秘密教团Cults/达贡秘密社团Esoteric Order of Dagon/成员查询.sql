-- 警告：此查询可能会暴露心智未准备好面对的真相。
-- 查询所有表现出“印斯茅斯外貌”第二阶段体征的教团成员。

SELECT
    member_name,
    initiation_date,
    bloodline_purity,
    physical_transformation_stage
FROM
    cult_members
WHERE
    cult_name = 'Esoteric Order of Dagon'
    AND physical_transformation_stage = 2
ORDER BY
    initiation_date DESC;

-- 查找所有与深潜者有过接触记录的船只。
SELECT
    vessel_name,
    last_seen_location,
    captain_name,
    reported_phenomenon
FROM
    shipping_logs
WHERE
    reported_phenomenon LIKE '%amphibious creature%'
    OR reported_phenomenon LIKE '%non-eucledian singing%';