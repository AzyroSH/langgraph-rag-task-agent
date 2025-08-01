-- 通过古代星图与洋流数据，重新计算拉莱耶的当前可能位置。
-- 此操作极度危险，可能引起目标的注意。

-- 定义变量：当前星辰位置 (Right Ascension, Declination)
DECLARE @RA_current REAL = 14.88;
DECLARE @DEC_current REAL = -47.23;

-- 查询历史记录中与当前星象最匹配的坐标点
SELECT TOP 1
    recorded_latitude,
    recorded_longitude,
    psychic_resonance_level,
    observation_date
FROM
    rlyeh_location_archive
WHERE
    star_map_RA BETWEEN (@RA_current - 0.5) AND (@RA_current + 0.5)
    AND star_map_DEC BETWEEN (@DEC_current - 0.5) AND (@DEC_current + 0.5)
ORDER BY
    psychic_resonance_level DESC;