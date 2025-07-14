CREATE TABLE Silver.Historical_Stock_News (
    id         INT             NULL,
    category   NVARCHAR(MAX)   NULL,
    datetime   DATETIME        NULL,
    headline   NVARCHAR(MAX)   NULL,
    image      NVARCHAR(MAX)   NULL,
    related    NVARCHAR(MAX)   NULL,
    source     NVARCHAR(MAX)   NULL,
    summary    NVARCHAR(MAX)   NULL,
    url        NVARCHAR(MAX)   NULL,
    symbol     NVARCHAR(MAX)   NULL
);
