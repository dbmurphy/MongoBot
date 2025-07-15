<!--
  Replace the image below with your project logo or banner.
  Example: ![MongoDB Atlas Slack Bot](docs/images/banner.png)
-->
<p align="center">
  <img src="docs/images/banner.png" alt="MongoDB Atlas Slack Bot" width="600"/>
</p>

<p align="center">
  <a href="https://python.org/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
  <a href="#build--development"><img src="https://img.shields.io/badge/build-passing-brightgreen.svg" alt="Build Status"></a>
</p>

# MongoDB Atlas Slack Bot

A professional Slack bot for managing MongoDB Atlas using natural language, powered by Claude 4 LLM and the MongoDB MCP server.

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Slack User    │────│  Slack Bot API  │────│  MongoDB Bot    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │ Command Handler │
                                               └─────────────────┘
                                                       │
                                    ┌──────────────────┼──────────────────┐
                                    ▼                  ▼                  ▼
                            ┌─────────────┐   ┌─────────────────────────────┐
                            │ Claude 4 LLM│   │        MCP Server           │
                            │ (Anthropic) │   │        (Node.js)            │
                            │             │   │                             │
                            │ • Intent    │   │ ┌─────────────────────────┐ │
                            │ • Response  │   │ │    MongoDB Atlas API    │ │
                            │ • Context   │   │ │                         │ │
                            └─────────────┘   │ │ • Clusters              │ │
                                              │ │ • Users                 │ │
                                              │ │ • IP Access Lists       │ │
                                              │ └─────────────────────────┘ │
                                              │ ┌─────────────────────────┐ │
                                              │ │      MongoDB            │ │
                                              │ │      Databases          │ │
                                              │ │                         │ │
                                              │ │ • Collections           │ │
                                              │ │ • Indexes               │ │
                                              │ │ • Documents             │ │
                                              │ └─────────────────────────┘ │
                                              └─────────────────────────────┘
```

---

## 🚀 Features
- **Atlas Management**: List, create, and monitor clusters
- **Security**: Manage IP access lists, users, and passwords
- **Performance Analysis**: Monitor clusters, analyze slow queries
- **Database Operations**: List databases/collections, schema analysis, CRUD
- **Index Optimization**: Detect missing and redundant indexes
- **Role-Based Access Control (RBAC)**: Admin/user/self-service roles, group-based permissions
- **Friendly Username Support**: Use Slack usernames, emails, or IDs for admin config
- **Real-Time Notifications & Audit Logging**
- **Personalized Help & RBAC Commands**

---

## 🔧 Key Components

### **MongoSlackBot Class** (`mongo_bot.py`)
- Handles Slack integration (Socket Mode)
- Manages MCP server connection
- Integrates with Claude 4 LLM
- Processes user messages and commands
- Formats responses for Slack

### **MongoCommandHandler Class** (`command_handler.py`)
- Parses natural language commands
- Extracts parameters (cluster names, IPs, time ranges)
- Maps commands to appropriate MCP tools
- Executes MongoDB operations
- Returns structured results

### **MongoDB MCP Server Integration**
- Uses `mongodb-mcp-server` npm package
- Supports all Atlas API operations
- Handles database operations
- Provides real-time data access

### **Claude 4 LLM Integration**
- Analyzes user intent
- Formats technical responses for Slack
- Provides contextual help and suggestions
- Handles error explanations

---

## 💬 Usage Examples

### Basic Commands

```
@mongobot List my clusters
```
```
🤖 **MongoDB Atlas Bot**
Found 3 clusters in your account:

• **production-cluster** (M10, us-east-1)
  Status: Active | Size: 10GB

• **staging-cluster** (M5, us-west-2)
  Status: Active | Size: 5GB

• **dev-cluster** (M0, us-east-1)
  Status: Active | Size: 512MB (Free Tier)
```

```
@mongobot Add IP 192.168.1.100 to the whitelist
```
```
🤖 **MongoDB Atlas Bot**
✅ Successfully added IP 192.168.1.100 to the access list.
This IP can now connect to all clusters in your project.
```

```
@mongobot help
```
```
🤖 **MongoDB Atlas Bot**
Here are your available commands:

**📊 Analysis & Monitoring:**
• List clusters and databases
• Analyze performance and slow queries
• View collection schemas and statistics

**🔐 Security:**
• Manage IP access lists (Admin & Self-service)
• Create database users (Admin only)
• Reset passwords (Admin & Self-service)

**📈 Optimization:**
• Find missing indexes
• Show redundant indexes
• *(Storage usage analysis - coming soon)*
• *(Query pattern optimization - coming soon)*

Type `@mongobot help [category]` for more details.
```

### Advanced Examples

> **Note:** Screenshots for advanced features like index analysis, performance monitoring, and RBAC management will be added here.
>
> **💡 Tip:** Run `make docs-images` to generate placeholder files for these screenshots.

<!-- Future screenshots will be added here:
- docs/images/index-analysis.png - Index analysis and optimization results
- docs/images/performance-monitoring.png - Performance monitoring dashboard
- docs/images/rbac-management.png - RBAC configuration and management
-->

---

## 🔌 Supported Commands

### Atlas Management
```
@mongobot List my clusters
@mongobot Create a new cluster called dev-cluster
@mongobot Show cluster details for production
@mongobot Connect to cluster staging
```

### Security Operations
```
@mongobot Add IP 192.168.1.100 to the whitelist
@mongobot Reset password for database user api-service
@mongobot Show current IP access list
@mongobot Create database user for application
```

### Performance Analysis
```
@mongobot Analyze cluster production performance over the last 24 hours
@mongobot Show slow queries on cluster analytics
@mongobot Group performance by cluster, nodeType, Node with summaries
@mongobot Performance issues on staging from last week
```

### Database Operations
```
@mongobot List all databases in cluster production
@mongobot Show collections in database ecommerce on cluster staging
@mongobot Analyze schema for collection users in cluster dev
@mongobot Get database statistics for inventory on cluster analytics
```

### Optimization
```
@mongobot Find missing indexes in database products on cluster production
@mongobot Find missing indexes on cluster production
@mongobot Show redundant indexes across all collections in cluster staging
@mongobot Show redundant indexes on cluster staging
```

> **💡 Tip:** When you specify a database (e.g., "in database products"), the analysis focuses on that database. When you omit the database specification, it analyzes ALL databases in the cluster for a comprehensive view.

> **🔮 Future Features:** Storage usage analysis and query pattern optimization are planned for future releases.

---

## 🛠️ MongoDB MCP Tools Used

### Atlas API Tools
- `atlas-list-orgs` - Organization management
- `atlas-list-projects` - Project management
- `atlas-list-clusters` - Cluster listing
- `atlas-inspect-cluster` - Cluster details
- `atlas-create-free-cluster` - Cluster creation
- `atlas-connect-cluster` - Cluster connection
- `atlas-inspect-access-list` - IP access management
- `atlas-create-access-list` - IP whitelist management
- `atlas-list-db-users` - Database user management
- `atlas-create-db-user` - User creation
- `atlas-list-alerts` - Alert management

### Database Tools
- `connect` - Database connection
- `find` - Document queries
- `aggregate` - Aggregation pipelines
- `list-databases` - Database listing
- `list-collections` - Collection listing
- `collection-indexes` - Index management
- `collection-schema` - Schema analysis
- `collection-storage-size` - Storage analysis
- `db-stats` - Database statistics
- `create-index` - Index creation
- `insert-one/many` - Document insertion
- `update-one/many` - Document updates
- `delete-one/many` - Document deletion

---

## ⚡ Quickstart

> **Tip:** For full build, test, and development instructions, see [BUILD.md](./BUILD.md).

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/MongoBot.git
   cd MongoBot
   ```
2. **Install dependencies & set up environment**
   ```bash
   make setup
   cp config.example.py config.py  # Edit config.py with your credentials
   ```
3. **Start the bot**
   ```bash
   make run
   ```

---

## 🔐 RBAC & Permissions
- **Admins:** Full access to all operations
- **Users:** Read-only and analysis operations
- **Self-service:** Password reset, profile info, add own IP to whitelist
- **Personalized help:** `@mongobot help` shows your available commands

---

## 📄 Documentation
- **Build & Development:** [BUILD.md](./BUILD.md)
- **Contributing:** [CONTRIBUTE.md](./CONTRIBUTE.md)

---

## 🗂️ Project Structure

```text
MongoBot/
├── mongo_bot.py           # Main Slack bot application
├── command_handler.py     # Natural language command processing
├── rbac.py               # Role-based access control
├── requirements.txt       # Python dependencies
├── requirements-dev.txt   # Development dependencies
├── config.example.py      # Configuration template
├── config.py              # Your configuration (not in repo)
├── test_bot.py            # Test suite
├── setup.py               # Automated setup script
├── setup-env.sh           # Python environment setup
├── .python-version        # Python version (3.10.15)
├── Makefile               # Build system
├── .pre-commit-config.yaml # Pre-commit hooks
├── .gitignore             # Git ignore patterns
├── .flake8                # Flake8 config
├── .pylintrc              # Pylint config
├── docs/                  # Documentation and images
│   └── images/            # Screenshots and graphics
├── README.md              # This file
├── BUILD.md               # Build/dev instructions
└── CONTRIBUTE.md          # Contribution guide
```

---

## 🔮 Future Enhancements
- **Storage usage analysis** - Database and collection storage metrics
- **Query pattern optimization** - Analyze and optimize query performance
- Time-based access controls
- Project-level permissions
- REST API endpoints
- Advanced auditing and logging
- Docker containerization
- CI/CD pipeline integration
- Real-time performance monitoring
- Automated index recommendations

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

---

<p align="center">
  <b>For build, test, and development instructions, see <a href="./BUILD.md">BUILD.md</a>.<br>
  For contributing, see <a href="./CONTRIBUTE.md">CONTRIBUTE.md</a>.</b>
</p>
