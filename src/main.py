import platform, os
from actions import configuration
if 'armv7l' in platform.platform():
    import main
    main.Myassistant().main()
elif configuration['Gpios']['control']=='Enabled' and 'armv7l' not in platform.platform():
    import new_start
    new_start.main()
else:
    import start
    start.main()

