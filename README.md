# rabbitmq-spout
use rabbitmq instead of kafka in spout
storm use kafka for default brokers, but it is frequently write its status to zookeeper, which made zookeeper client timeout and retry many times,finally lose connection.
To solve this problems, here use rabbitmq to avoid this problems.
