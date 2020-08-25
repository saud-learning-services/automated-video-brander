from termcolor import cprint

import watermark
import stitch

if __name__ == '__main__':
    watermark.process_body_clips()
    stitch.main()
    cprint('\nCOMPLETED', 'green')
    cprint('\nMade by Marko Prodanovic\n', 'yellow')
