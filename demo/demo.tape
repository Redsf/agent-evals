# Terminal demo for the README. Rebuild with:  vhs demo/demo.tape
# Requires VHS (https://github.com/charmbracelet/vhs) and this package installed: pip install -e .
Output demo/demo.gif
Require agent-eval
Set Shell "bash"
Set FontFamily "JetBrains Mono"
Set FontSize 17
Set Width 1300
Set Height 580
Set Padding 28
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 35ms
Set Framerate 24

Hide
Type "python demo/regressed_target.py & sleep 1; clear" Enter
Sleep 1500ms
Show

Type "# A prompt change just shipped. Run the eval suite before it goes live:" Sleep 300ms Enter
Type `agent-eval run demo/support.suite.json --no-llm; echo "exit code: $?"` Sleep 400ms Enter
Sleep 5s

Hide
Type `kill %1; python examples/mock_target.py >/dev/null & sleep 1; clear` Enter
Sleep 1500ms
Show

Type "# Prompt fixed. Same suite, same command:" Sleep 300ms Enter
Type `agent-eval run demo/support.suite.json --no-llm; echo "exit code: $?"` Sleep 400ms Enter
Sleep 4s

Hide
Type "kill %1" Enter
