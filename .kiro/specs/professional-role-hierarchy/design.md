# Professional Role Hierarchy - Design Document

## Overview

The Professional Role Hierarchy system transforms the Telegram Operations Automation System from a simple 4-role structure (OWNERS, ADMINISTRATORS, MANAGERS, QA_REVIEWERS) into a comprehensive 9-tier professional hierarchy organized across 5 organizational tiers. This design provides granular permission mapping, role-based analytics, hierarchical authority validation, and complete audit trails while maintaining backward compatibility during migration.

### Design Goals

1. **Industry-Standard Structure**: Implement a professional hierarchy that reflects real-world organizational structures
2. **Granular Permissions**: Map each professional title to specific system capabilities
3. **Hierarchical Authority**: Enforce organizational authority where higher tiers can override lower-tier decisions
4. **Backward Compatibility**: Support gradual migration from legacy roles without service disruption
5. **Audit Transparency**: Track all role assignments and changes with immutable audit trails
6. **Analytics Integration**: Enable performance reporting grouped by organizational tier and professional title

### Key Design Decisions

- **Enum-Based Titles**: Use Python Enum for type-safe professional title definitions
- **Tier-Based Grouping**: Organize titles into 5 organizational tiers for analytics and permission inheritance
- **Dual Configuration**: Support both .env-based and database-stored role assignments
- **Migration-First Approach**: Prioritize smooth transition with automatic legacy role mapping
- **Permission Matrix**: Centralize all permission logic in AccessControl component
- **Immutable Audit**: Store role changes in append-only audit trail

## Architecture

### System Components

```mermaid
graph TB
    subgraph "Configuration Layer"
        ENV[.env File]
        CONFIG[Config System]
    end
    
    subgraph "Data Layer"
        USER_MODEL[User Model]
        USER_REPO[User Repository]
        AUDIT_MODEL[RoleChange Model]
        AUDIT_REPO[Audit Repository]
        DB[(SQLite Database)]
    end
    
    subgraph "Security Layer"
        ACCESS[Access Control]
        PERM_MATRIX[Permission Matrix]
    end
    
    subgraph "Service Layer"
        ROLE_SERVICE[Role Service]
        ANALYTICS[Role Analytics]
    end
    
    subgraph "Bot Layer"
        CMD_HANDLER[Command Handler]
        BOT[Telegram Bot]
    end
    
    ENV --> CONFIG
    CONFIG --> ACCESS
    CONFIG --> ROLE_SERVICE
    
    USER_MODEL --> USER_REPO
    AUDIT_MODEL --> AUDIT_REPO
    USER_REPO --> DB
    AUDIT_REPO --> DB
    
    ACCESS --> PERM_MATRIX
    ACCESS --> USER_REPO
    
    ROLE_SERVICE --> USER_REPO
    ROLE_SERVICE --> AUDIT_REPO
    ROLE_SERVICE --> ACCESS
    
    ANALYTICS --> USER_REPO
    ANALYTICS --> AUDIT_REPO
    
    CMD_HANDLER --> ROLE_SERVICE
    CMD_HANDLER --> ACCESS
    BOT --> CMD_HANDLER
