CREATE TABLE Gold.Historical_Stock_News_Sentiment_Score (
    id              INT             NOT NULL,
    category        NVARCHAR(255)   NULL,
    datetime        NVARCHAR(50)    NULL,
    headline        NVARCHAR(MAX)   NULL,
    image           NVARCHAR(2083)  NULL,
    related         NVARCHAR(255)   NULL,
    source          NVARCHAR(255)   NULL,
    summary         NVARCHAR(MAX)   NULL,
    url             NVARCHAR(2083)  NULL,
    symbol          NVARCHAR(50)    NULL,
    positive_value  FLOAT           NULL,
    negative_value  FLOAT           NULL,
    neutral_value   FLOAT           NULL
);
