# Database Architecture, Scale, and NoSQL with Elasticsearch

The Database Architecture, Scale, and NoSQL with Elasticsearch course by UMich through Coursera

---

## Overview

In this comprehensive module, we will explore the fundamental principles of database architecture and examine how modern applications achieve scale, reliability, and performance through strategic architectural decisions.

### Database Architecture and Scalability

We begin by examining **database deployment strategies** and **replication architectures** that enable applications to handle massive scale:

- **Master-Slave Replication**: Understanding read scaling, failover mechanisms, and data consistency challenges
- **Master-Master Replication**: Exploring bi-directional replication, conflict resolution, and distributed write scenarios
- **Sharding Strategies**: Horizontal partitioning techniques for distributing data across multiple database instances
- **Performance Impact Analysis**: How each architectural pattern affects throughput, latency, and system reliability

### NoSQL Databases: Elasticsearch as a Case Study

We will then dive deep into **NoSQL database paradigms** using **Elasticsearch** as our primary example. Elasticsearch represents a powerful class of document-oriented databases that communicate primarily through JSON APIs. 

**Why Elasticsearch?** It exemplifies a common real-world architectural pattern - the **polyglot persistence** approach where organizations leverage:

- **Elasticsearch** for full-text search, analytics, and real-time data exploration
- **PostgreSQL** for transactional integrity, complex relationships, and structured data operations

This hybrid approach allows applications to utilize the strengths of each database type while mitigating their respective limitations.

### ACID vs BASE: Fundamental Database Paradigms

Finally, we will conduct a comprehensive comparison between two foundational database consistency models:

#### ACID (Strong Consistency Model)
**PostgreSQL and traditional RDBMS approach:**
- **Atomicity**: Transactions are all-or-nothing operations
- **Consistency**: Database remains in a valid state after transactions
- **Isolation**: Concurrent transactions don't interfere with each other
- **Durability**: Committed changes persist permanently

#### BASE (Eventual Consistency Model)
**Elasticsearch and distributed NoSQL approach:**
- **Basic Availability**: System remains operational despite failures
- **Soft State**: Data consistency is not guaranteed at any given time
- **Eventual Consistency**: System will become consistent over time

### Learning Outcomes

Through practical examples and architectural analysis, you will gain the expertise to:
- Design scalable database architectures for different application requirements
- Choose appropriate replication strategies based on consistency and performance needs
- Evaluate when to use SQL vs NoSQL databases in system design
- Implement polyglot persistence patterns in modern applications
- Make informed trade-offs between consistency, availability, and partition tolerance (CAP theorem)

---

## Lecture Notes

Click [here](https://www.pg4e.com/lectures/)
- [Database Architecture](https://www.pg4e.com/lectures/07-Architecture.pptx)
- [Introduction to Elasticsearch](https://www.pg4e.com/lectures/07-Elastic.pptx)

---

## Topics

- [Database Architecture: From ACID to BASE](database-architecture.md)
- [Introduction to Python Elasticsearch](elasticsearch.md)