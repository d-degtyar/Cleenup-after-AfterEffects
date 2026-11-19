# Release Notes - After Effects Project Cleanup Tool

## Version 1.0.1 - Safety fix

### Fixed
- **Sequences no longer take unrelated files with them.** Deleting a sequence removed its whole
  folder, and moving one moved the whole folder, including any other files that lived there.
  Now only the sequence frames (and their auxiliary files) are deleted or moved; the folder is
  removed only if it is left empty.
- The processed size of sequences was reported as 0 after a real delete, and the total size was
  shown in bytes labelled as MB.
- The confirmation dialog counted only single files, not sequences.

### Added
- A warning before a real run when After Effects is open: the files an open project uses are
  locked and would be skipped.
- Skipped files now show the reason, including "used by another program" for locked files.
- Tests for the sequence handling (`python -m pytest tests`).

## Version 1.0.0 - Initial Release

### 🎉 New Features

#### Core Functionality
- **Intelligent File Sequence Processing** - Automatic recognition and handling of file sequences (e.g., `image_[00001-00100].png`) as single units
- **Dual Operation Modes** - Support for both file deletion and moving operations
- **Advanced Report Parsing** - Compatible with both old After Effects reports (with status indicators) and new simple file list formats
- **Comprehensive Filtering System** - File type exclusion, size-based filtering, and custom rules

#### User Interface
- **Modern GUI Interface** - Intuitive tkinter-based interface with real-time progress tracking
- **Interactive Configuration** - Easy-to-use controls for all operation parameters
- **Visual Progress Indicators** - Real-time progress bars and status updates
- **Auto-Report Detection** - Automatic discovery and loading of report files

#### Safety & Security
- **Dry Run Mode** - Test operations without making actual changes
- **Backup Lists** - Automatic creation of operation logs for recovery purposes
- **Detailed Logging** - Comprehensive logging of all operations and errors
- **Project File Protection** - Optional preservation of .aep and other project files

#### Reporting & Analytics
- **HTML Report Generation** - Beautiful, detailed reports with statistics and operation summaries
- **JSON Export** - Machine-readable operation data for further processing
- **Disk Usage Statistics** - Before/after disk space analysis
- **Operation History** - Track and review previous cleanup operations

### 🛠️ Technical Features

#### Architecture
- **Modular Design** - Clean separation between GUI, core logic, and utilities
- **Cross-Platform Compatibility** - Primary support for Windows 10/11
- **Python 3.7+ Support** - Compatible with modern Python versions
- **Standard Library Only** - No external dependencies required

#### File Processing
- **Smart Sequence Detection** - Advanced algorithms for identifying file sequences
- **Robust Error Handling** - Graceful handling of file access errors and edge cases
- **Memory Efficient** - Optimized for processing large file lists
- **Unicode Support** - Full support for international file names and paths

### 📁 Project Structure

```
ae-cleanup-tool/
├── ae_cleanup_gui.py          # Main GUI application
├── ae_cleanup_core.py         # Core processing logic
├── ae_sequence_parser.py      # File sequence detection and parsing
├── ae_report_generator.py     # HTML/JSON report generation
├── ae_cleanup_improved.bat    # Windows batch launcher
├── empty-folder-cleaner-absolute.bat  # Utility for empty folder cleanup
├── requirements.txt           # Project dependencies (standard library only)
├── README.md                 # Comprehensive documentation
├── .gitignore                # Git ignore rules
└── RELEASE_NOTES.md          # This file
```

### 🚀 Getting Started

1. **Prerequisites**: Python 3.7+ with tkinter (included in standard installation)
2. **Installation**: Clone repository or download release package
3. **Usage**: Run `python ae_cleanup_gui.py` to start the application
4. **Report Generation**: Use After Effects `File > Dependencies > Collect Files > Generate Report Only`

### 🔧 Configuration Options

- **Operation Type**: Delete or Move files
- **Target Directory**: Destination for move operations
- **File Filters**: Exclude specific file types or size ranges
- **Sequence Processing**: Enable/disable intelligent sequence handling
- **Safety Options**: Dry run mode, backup creation, project file preservation
- **Logging Level**: Control detail level of operation logs

### 📊 Supported Report Formats

1. **Classic After Effects Reports** - Reports with "missing" or "відсутній" status indicators
2. **Simple File Lists** - Plain text files with absolute file paths
3. **Mixed Format Detection** - Automatic format recognition and appropriate parsing

### 🛡️ Safety Features

- **Non-Destructive Testing** - Dry run mode for safe operation preview
- **Automatic Backups** - JSON-formatted backup lists for all operations
- **Error Recovery** - Detailed error logging and graceful failure handling
- **User Confirmation** - Clear confirmation dialogs for destructive operations

### 📈 Performance

- **Optimized for Large Projects** - Efficient handling of thousands of files
- **Memory Management** - Low memory footprint even with large file lists
- **Progress Tracking** - Real-time updates during long operations
- **Responsive UI** - Non-blocking interface during file operations

### 🌐 Internationalization

- **Multi-Language Support** - Interface available in English and Ukrainian
- **Unicode File Handling** - Full support for international file names
- **Localized Error Messages** - Error reporting in user's preferred language

### 🔮 Future Roadmap

- **Plugin System** - Extensible architecture for custom processing rules
- **Network Drive Support** - Enhanced handling of network-attached storage
- **Batch Processing** - Multiple report processing in single operation
- **Advanced Filtering** - Regular expression and date-based filtering
- **Cloud Integration** - Support for cloud storage providers

### 📝 Known Limitations

- **Primary Platform**: Optimized for Windows; limited testing on other platforms
- **GUI Framework**: Uses tkinter; may have platform-specific appearance differences
- **Large File Handling**: Very large files (>2GB) may require additional processing time

### 🤝 Contributing

This project welcomes contributions! Please see README.md for development guidelines and contribution instructions.

### 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

### 🙏 Acknowledgments

- After Effects community for feedback and testing
- Python tkinter developers for the GUI framework
- Contributors and beta testers

---

**Note**: This is the initial release. Please report any issues or feature requests through the project's GitHub repository.