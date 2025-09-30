# Changelog

All notable changes to the Nest Protect MCP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-20

### 🎉 **Production Release**

### Added
- **Enhanced Logging System**: Comprehensive debugging and monitoring capabilities
- **Pydantic V2 Migration**: Complete migration to modern Pydantic patterns
- **Production Stability**: Server runs without crashes or disconnections
- **Claude Desktop Integration**: Fixed configuration issues for stable operation

### Changed
- **BREAKING**: Updated all Pydantic models to V2 patterns (`field_validator`, `ConfigDict`)
- **BREAKING**: Enhanced logging format with detailed startup/shutdown tracking
- **BREAKING**: Removed `--kill` argument from production configuration
- Updated FastMCP to version 2.12.3
- Improved error handling with detailed stack traces
- Enhanced tool registration logging

### Fixed
- **Critical**: Eliminated `PydanticDeprecatedSince20` warnings
- **Critical**: Fixed server disconnection issues in Claude Desktop
- **Critical**: Resolved configuration problems causing immediate shutdowns
- Fixed import errors in Pydantic model definitions
- Fixed JSON encoder deprecation warnings
- Improved server lifecycle management

### Security
- Enhanced error handling to prevent information leakage
- Improved authentication flow stability

## [0.2.0] - 2025-09-19

### Added
- Initial implementation of the Nest Protect MCP server
- Support for real-time monitoring of Nest Protect devices
- OAuth 2.0 authentication with Google's Smart Device Management API
- Device state management and event system
- Command support for hushing alarms and running tests
- Comprehensive documentation and setup guide
- Enhanced configuration management

### Fixed
- Lint errors and code style issues
- Dependencies management in the build process
- Documentation formatting and completeness

## [0.1.0] - 2025-08-26
### Added
- Initial release of Nest Protect MCP server
- Basic device monitoring and control functionality
- Configuration management
- API documentation

[Unreleased]: https://github.com/yourusername/nest-protect-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/nest-protect-mcp/releases/tag/v0.1.0
