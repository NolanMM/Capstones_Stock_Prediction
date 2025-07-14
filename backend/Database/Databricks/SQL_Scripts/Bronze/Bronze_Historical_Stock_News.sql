CREATE TABLE Bronze.Historical_Stock_News (
    id         BIGINT              NOT NULL,
    category   VARCHAR(50)         NULL,
    datetime   DATETIME2           NULL,
    headline   VARCHAR(500)        NULL,
    image      VARCHAR(1000)       NULL,
    related    VARCHAR(100)        NULL,
    source     VARCHAR(100)        NULL,
    summary    VARCHAR(5000)       NULL,
    url        VARCHAR(1000)       NULL,
    symbol     VARCHAR(100)        NULL
);
