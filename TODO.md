# n8n-deploy TODO

This file tracks planned features and improvements for the n8n-deploy project.

## 🗄️ Database & Storage

### Alternative Database Support
- **Alternative database configuration (mysql/mariadb, postgres, mongodb)**
  - Abstract database layer to support multiple backends
  - MySQL/MariaDB adapter with connection pooling
  - PostgreSQL adapter with async support
  - MongoDB adapter for document-based storage
  - Database migration utilities between backends
  - Configuration-driven database selection
  - Performance benchmarking across database types

## 🔒 Security & Data Protection

### Workflow Encryption
- **Save workflows in DB key-encrypted with user-specified key, update on every push/pull**
  - Implement user-specified encryption key support
  - Encrypt workflow JSON content before storing in SQLite database
  - Decrypt workflows on read operations
  - Update encrypted workflow on every push/pull operation
  - Provide key rotation capabilities
  - Consider integration with system keychain/keyring for key storage

## 🐳 Deployment & Distribution

### Docker Support
- **Dockerize application, create image, publish**
  - Create optimized Docker image for n8n-deploy
  - Volume mounts for workflow directories and file-based database
  - Docker Compose examples for common setups
  - Publish to Docker Hub and GitHub Container Registry

## ⚙️ Setup & Configuration

### Configuration Wizard
- **Configuration wizard for first-time setup**
  - Interactive setup
  - Database initialization with options
  - Directory structure creation and validation
  - n8n server connection testing
  - API key setup and validation
  - Default workflow directory detection
  - Configuration file generation

## 🧪 Testing & Quality Assurance

### Unit Test Coverage Improvements
Current coverage: 39% overall (51 unit tests)

**CLI Testing**
- Command execution with various parameter combinations
- More error handling and validation scenarios
- Help and version display functionality
- Configuration file handling and validation
- Backup/restore command edge cases
- Database management command error scenarios
- API key command validation and error handling
- Output formatting consistency (emoji vs no-emoji modes)
- Global flag processing and precedence

**Database Layer Testing**
- Schema initialization and migration testing
- Concurrent access and transaction safety
- Connection retry logic and timeout handling
- Database corruption recovery scenarios
- Backup integrity verification
- Large dataset performance testing
- Schema version compatibility testing
- Error recovery and rollback mechanisms

**WorkflowManager Testing**
- Workflow CRUD operations edge cases
- File validation and JSON parsing errors
- n8n server integration timeout scenarios
- Backup creation and restoration workflows
- Search functionality with various query types
- Statistics calculation and reporting
- Large workflow handling and memory usage
- Concurrent workflow operations

**API Key Management Testing**
- Key expiration handling and cleanup
- Usage tracking and analytics
- Key validation and format checking
- Environment variable fallback scenarios
- Concurrent key access patterns
- Key rotation and security scenarios

### Integration Test Enhancements
- End-to-end workflow lifecycle testing
- Cross-platform compatibility testing (Windows, macOS, Linux)
- Performance regression testing with large datasets
- Memory leak detection in long-running operations
- Network resilience testing for server operations
- Configuration migration testing between versions

### Performance & Load Testing
- Benchmark suite for critical operations
- Memory usage profiling for large workflows
- Database performance with thousands of workflows
- Concurrent user simulation testing
- Startup time optimization verification

### Security Testing
- Input validation and injection attack prevention
- File path traversal vulnerability testing
- API key exposure prevention testing
- Temporary file security verification
- Configuration file permission testing

## 🔮 Future Enhancements

### Workflow Management
- Advanced workflow search
- Bulk operations for multiple workflows
- Workflow templates and boilerplate generation

### Integration & Sync
- Git integration for workflow version control
- Multi-server synchronization capabilities

### User Experience
- Interactive TUI mode for workflow management
- Progress bars for long-running operations
- Shell completion for bash/zsh/fish

### Performance & Scalability
- Concurrent operations for large workflow sets
- Database optimization for large datasets
- Caching layer for frequently accessed workflows
- Background sync operations

---

## 📊 Testing Metrics & Goals

**Current Status:**
- Unit Tests: 51 tests, 39% coverage
- Integration Tests: 174+ tests (comprehensive E2E coverage)
- Critical Paths: Database, CLI, and Manager need significant unit test expansion

**Target Goals:**
- Unit Test Coverage: 80%+ for critical modules
- CLI Coverage: 60%+ (currently 26%)
- Database Coverage: 80%+ (currently 43%)
- Manager Coverage: 70%+ (currently 35%)

**Immediate Actions:**
1. Add database unit tests for schema management and concurrent access
2. Create CLI command unit tests for core functionality
3. Expand manager unit tests for workflow operations
4. Implement performance regression testing suite

---

*Last updated: 2025-09-28*
*Coverage analysis completed with detailed testing roadmap*
