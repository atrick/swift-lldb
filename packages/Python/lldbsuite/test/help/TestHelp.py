"""
Test some lldb help commands.

See also CommandInterpreter::OutputFormattedHelpText().
"""

from __future__ import print_function



import os, time
import lldb
from lldbsuite.test.decorators import *
from lldbsuite.test.lldbtest import *
from lldbsuite.test import lldbutil

class HelpCommandTestCase(TestBase):

    mydir = TestBase.compute_mydir(__file__)

    @no_debug_info_test
    def test_simplehelp(self):
        """A simple test of 'help' command and its output."""
        self.expect("help",
            startstr = 'Debugger commands:')

        self.expect("help -a", matching=False,
                    substrs = ['next'])
        
        self.expect("help", matching=True,
                    substrs = ['next'])
    
    @no_debug_info_test
    def test_help_on_help(self):
        """Testing the help on the help facility."""
        self.expect("help help", matching=True,
                    substrs = ['--hide-aliases',
                               '--hide-user-commands'])

    @no_debug_info_test
    def version_number_string(self):
        """Helper function to find the version number string of lldb."""
        plist = os.path.join(os.environ["LLDB_SRC"], "resources", "LLDB-Info.plist")
        try:
            CFBundleVersionSegFound = False
            with open(plist, 'r') as f:
                for line in f:
                    if CFBundleVersionSegFound:
                        version_line = line.strip()
                        import re
                        m = re.match("<string>(.*)</string>", version_line)
                        if m:
                            version = m.group(1)
                            return version
                        else:
                            # Unsuccessful, let's juts break out of the for loop.
                            break

                    if line.find("<key>CFBundleVersion</key>") != -1:
                        # Found our match.  The next line contains our version
                        # string, for example:
                        # 
                        #     <string>38</string>
                        CFBundleVersionSegFound = True

        except:
            # Just fallthrough...
            import traceback
            traceback.print_exc()
            pass

        # Use None to signify that we are not able to grok the version number.
        return None

    @no_debug_info_test
    def test_help_arch(self):
        """Test 'help arch' which should list of supported architectures."""
        self.expect("help arch",
            substrs = ['arm', 'x86_64', 'i386'])

    @no_debug_info_test
    def test_help_version(self):
        """Test 'help version' and 'version' commands."""
        self.expect("help version",
            substrs = ['Show the LLDB debugger version.'])

        valid_version_patterns = []

        # Add the Swift OSS version pattern
        valid_version_patterns.extend([
            # It's okay for the local build to not have a date.  This happens in Xcode builds.
            r"^lldb-local(-\d{4}-\d{2}-\d{2})? \((LLDB [^,)]+(, (LLVM|Clang|Swift-\d+\.\d+) [^,)]+){0,3})?\)$",
            # But it's not okay for the buildbot to be missing a date.  This shouldn't happen in a build-script-based build.
            r"^lldb-buildbot-\d{4}-\d{2}-\d{2} \((LLDB [^,)]+(, (LLVM|Clang|Swift-\d+\.\d+) [^,)]+){0,3})?\)$",
            ]
            )

        # Add valid llvm.org and official Apple Xcode LLDB version patterns
        version_str = self.version_number_string()
        import re
        match = re.match('[0-9]+', version_str)
        if sys.platform.startswith("darwin"):
            valid_version_patterns.append(
                '^lldb-' + (version_str if match else '[0-9]+'))
        else:
            valid_version_patterns.append('^lldb version (\d|\.)+.*$')

        match = self.match("version", valid_version_patterns)
        self.assertIsNotNone(
            match, "version result did not match any valid version string")
        # print("matched: {}".format(match.re.pattern))

    @no_debug_info_test
    def test_help_should_not_crash_lldb(self):
        """Command 'help disasm' should not crash lldb."""
        self.runCmd("help disasm", check=False)
        self.runCmd("help unsigned-integer")

    @no_debug_info_test
    def test_help_should_not_hang_emacsshell(self):
        """Command 'settings set term-width 0' should not hang the help command."""
        self.expect("settings set term-width 0",
                    COMMAND_FAILED_AS_EXPECTED, error=True,
            substrs = ['error: 0 is out of range, valid values must be between'])
        # self.runCmd("settings set term-width 0")
        self.expect("help",
            startstr = 'Debugger commands:')

    @no_debug_info_test
    def test_help_breakpoint_set(self):
        """Test that 'help breakpoint set' does not print out redundant lines of:
        'breakpoint set [-s <shlib-name>] ...'."""
        self.expect("help breakpoint set", matching=False,
            substrs = ['breakpoint set [-s <shlib-name>]'])

    @no_debug_info_test
    def test_help_image_dump_symtab_should_not_crash(self):
        """Command 'help image dump symtab' should not crash lldb."""
        # 'image' is an alias for 'target modules'.
        self.expect("help image dump symtab",
            substrs = ['dump symtab',
                       'sort-order'])

    @no_debug_info_test
    def test_help_image_du_sym_is_ambiguous(self):
        """Command 'help image du sym' is ambiguous and spits out the list of candidates."""
        self.expect("help image du sym",
                    COMMAND_FAILED_AS_EXPECTED, error=True,
            substrs = ['error: ambiguous command image du sym',
                       'symfile',
                       'symtab'])

    @no_debug_info_test
    def test_help_image_du_line_should_work(self):
        """Command 'help image du line-table' is not ambiguous and should work."""
        # 'image' is an alias for 'target modules'.
        self.expect("help image du line",
            substrs = ['Dump the line table for one or more compilation units'])

    @no_debug_info_test
    def test_help_target_variable_syntax(self):
        """Command 'help target variable' should display <variable-name> ..."""
        self.expect("help target variable",
            substrs = ['<variable-name> [<variable-name> [...]]'])

    @no_debug_info_test
    def test_help_watchpoint_and_its_args(self):
        """Command 'help watchpoint', 'help watchpt-id', and 'help watchpt-id-list' should work."""
        self.expect("help watchpoint",
            substrs = ['delete', 'disable', 'enable', 'list'])
        self.expect("help watchpt-id",
            substrs = ['<watchpt-id>'])
        self.expect("help watchpt-id-list",
            substrs = ['<watchpt-id-list>'])

    @no_debug_info_test
    def test_help_watchpoint_set(self):
        """Test that 'help watchpoint set' prints out 'expression' and 'variable'
        as the possible subcommands."""
        self.expect("help watchpoint set",
            substrs = ['The following subcommands are supported:'],
            patterns = ['expression +--',
                        'variable +--'])

    @no_debug_info_test
    def test_help_po_hides_options(self):
        """Test that 'help po' does not show all the options for expression"""
        self.expect("help po",
            substrs = ['--show-all-children', '--object-description'], matching=False)

    @no_debug_info_test
    def test_help_run_hides_options(self):
        """Test that 'help run' does not show all the options for process launch"""
        self.expect("help run",
            substrs = ['--arch', '--environment'], matching=False)

    @no_debug_info_test
    def test_help_next_shows_options(self):
        """Test that 'help next' shows all the options for thread step-over"""
        self.expect("help next",
            substrs = ['--python-class','--run-mode'], matching=True)

    @no_debug_info_test
    def test_help_provides_alternatives(self):
        """Test that help on commands that don't exist provides information on additional help avenues"""
        self.expect("help thisisnotadebuggercommand",
            substrs = ["'thisisnotadebuggercommand' is not a known command.",
            "Try 'help' to see a current list of commands.",
            "Try 'apropos thisisnotadebuggercommand' for a list of related commands.",
            "Try 'type lookup thisisnotadebuggercommand' for information on types, methods, functions, modules, etc."], error=True)

        self.expect("help process thisisnotadebuggercommand",
            substrs = ["'process thisisnotadebuggercommand' is not a known command.",
            "Try 'help' to see a current list of commands.",
            "Try 'apropos thisisnotadebuggercommand' for a list of related commands.",
            "Try 'type lookup thisisnotadebuggercommand' for information on types, methods, functions, modules, etc."])

    @no_debug_info_test
    def test_custom_help_alias(self):
        """Test that aliases pick up custom help text."""
        def cleanup():
            self.runCmd('command unalias afriendlyalias', check=False)
            self.runCmd('command unalias averyfriendlyalias', check=False)
        
        self.addTearDownHook(cleanup)
        self.runCmd('command alias --help "I am a friendly alias" -- afriendlyalias help')
        self.expect("help afriendlyalias", matching=True, substrs = ['I am a friendly alias'])
        self.runCmd('command alias --long-help "I am a very friendly alias" -- averyfriendlyalias help')
        self.expect("help averyfriendlyalias", matching=True, substrs = ['I am a very friendly alias'])
