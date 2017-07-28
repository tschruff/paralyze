"""

"""

SETTINGS = {
    "WORKSPACE_CONFIG_DIR": ".paralyze",
    "WORKSPACE_CONFIG_FILE": "config.json",
    "WORKSPACE_CONFIG": {
        "logging": {
            "level": "WARNING",
            "file": "log.txt",
            "file_format": "[%(asctime)-15s][%(levelname)-7s] %(message)s"
        }
    },

    "TEMPLATE_WORKSPACE_CONFIG": {
        "template": {
            "environment": {
                "block_start_string": "{%",
                "block_end_string": "%}",
                "variable_start_string": "{{",
                "variable_end_string": "}}",
                "comment_start_string": "{#",
                "comment_end_string": "#}",
                "line_statement_prefix": None,
                "line_comment_prefix": "//",
                "trim_blocks": False,
                "lstrip_blocks": False,
                "newline_sequence": "\n",
                "keep_trailing_newline": False,
                "extensions": "",
                "optimized": True,
                "autoescape": False,
                "cache_size": 400,
                "auto_reload": True,
                "enable_async": True
            },
            "loader": {
                "dirs": [],
                "follow_links": True,
                "encoding": "utf-8"
            },
            "context_extension_dirs": []
        },
        "parameter_module": "",
        "logging": {
            "level": "WARNING",
            "file": "log.txt",
            "file_format": "[%(asctime)-15s][%(levelname)-7s] %(message)s"
        }
    }
}
