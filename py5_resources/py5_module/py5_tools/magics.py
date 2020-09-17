import time
import io
from pathlib import Path
import tempfile

from IPython.display import display, SVG, Image
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

import PIL

from .run import run_single_frame_sketch


def wait(wait_time, sketch):
    end_time = time.time() + wait_time
    while time.time() < end_time and sketch.is_running:
        time.sleep(0.2)


class BaseHook:

    def __init__(self, hook_name):
        self.hook_name = hook_name
        self.is_ready = False
        self.exception = None
        self.is_terminated = False

    def hook_finished(self, sketch):
        sketch._remove_post_hook('draw', self.hook_name)
        self.is_ready = True

    def hook_error(self, sketch, e):
        self.exception = e
        sketch._remove_post_hook('draw', self.hook_name)
        self.is_terminated = True

    def sketch_terminated(self):
        self.is_terminated = True


class ScreenshotHook(BaseHook):

    def __init__(self, filename):
        super().__init__('py5screenshot_hook')
        self.filename = filename

    def __call__(self, sketch):
        try:
            sketch.save_frame(self.filename)
            self.hook_finished(sketch)
        except Exception as e:
            self.hook_error(sketch, e)


class SaveFramesHook(BaseHook):

    def __init__(self, dirname, filename, start, limit):
        super().__init__('py5save_frames_hook')
        self.dirname = dirname
        self.filename = filename
        self.start = start
        self.limit = limit
        self.num_offset = None
        self.filenames = []

    def __call__(self, sketch):
        try:
            if self.num_offset is None:
                self.num_offset = 0 if self.start is None else sketch.frame_count - self.start
            num = sketch.frame_count - self.num_offset
            frame_filename = sketch._insert_frame(
                str(self.dirname / self.filename), num=num)
            sketch.save_frame(frame_filename)
            self.filenames.append(frame_filename)
            if len(self.filenames) == self.limit:
                self.hook_finished(sketch)
        except Exception as e:
            self.hook_error(sketch, e)


class GrabFramesHook(BaseHook):

    def __init__(self, delay, count):
        super().__init__('py5grab_frames_hook')
        self.delay = delay
        self.count = count
        self.frames = []
        self.last_frame_time = 0

    def __call__(self, sketch):
        try:
            if time.time() - self.last_frame_time < self.delay / 1000:
                return
            sketch.load_np_pixels()
            self.frames.append(sketch.np_pixels[:, :, 1:].copy())
            self.last_frame_time = time.time()
            if len(self.frames) == self.count:
                self.hook_finished(sketch)
        except Exception as e:
            self.hook_error(sketch, e)


@magics_class
class Py5Magics(Magics):

    def _filename_check(self, filename):
        filename = Path(filename)
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True)
        return filename

    @magic_arguments()
    @argument('width', type=int, help='width of PDF output')
    @argument('height', type=int, help='height of PDF output')
    @argument('filename', type=str, help='filename for PDF output')
    @argument('--unsafe', dest='unsafe', action='store_true',
              help="allow new variables to enter the global namespace, creating a potentially unsafe situation")
    @cell_magic
    def py5drawpdf(self, line, cell):
        """Create a PDF with py5.

        For users who are familiar with Processing and py5 programming, you can
        pretend the code in this cell will be executed in a sketch with no
        `draw()` function and your code in the `setup()` function. It will use
        the PDF renderer.

        The below example will create a red square on a gray background:

        ```
            %%py5drawpdf 500 250 /tmp/test.pdf
            py5.background(128)
            py5.fill(255, 0, 0)
            py5.rect(80, 100, 50, 50)
        ```

        As this is creating a PDF, you cannot do operations on the
        `pixels` or `np_pixels` arrays. Use `%%py5draw` instead.

        Code used in this cell can reference functions and variables defined in
        other cells. By default, variables and functions created in this cell
        will be local to only this cell because to do otherwise would be unsafe.
        If you understand the risks, you can use the `global` keyword to add a
        single function or variable to the notebook namespace or the --unsafe
        argument to add everything to the notebook namespace. Either option may
        be very useful to you, but be aware that using py5 objects in a
        different notebook cell or reusing them in another sketch can result in
        nasty errors and bizzare consequences. Any and all problems resulting
        from using these features are solely your responsibility and not the py5
        library maintainers.
        """
        args = parse_argstring(self.py5drawpdf, line)
        pdf = run_single_frame_sketch('PDF', cell, args.width, args.height,
                                      self.shell.user_ns, not args.unsafe)
        if pdf:
            filename = self._filename_check(args.filename)
            with open(filename, 'wb') as f:
                f.write(pdf)
            print(f'PDF written to {filename}')

    @magic_arguments()
    @argument('width', type=int, help='width of DXF output')
    @argument('height', type=int, help='height of DXF output')
    @argument('filename', type=str, help='filename for DXF output')
    @argument('--unsafe', dest='unsafe', action='store_true',
              help="allow new variables to enter the global namespace, creating a potentially unsafe situation")
    @cell_magic
    def py5drawdxf(self, line, cell):
        """Create a DXF file with py5.

        For users who are familiar with Processing and py5 programming, you can
        pretend the code in this cell will be executed in a sketch with no
        `draw()` function and your code in the `setup()` function. It will use
        the DXF renderer.

        The below example will create a rotated cube:

        ```
           %%py5drawdxf 200 200 /tmp/test.dxf
            py5.translate(py5.width / 2, py5.height / 2)
            py5.rotate_x(0.4)
            py5.rotate_y(0.8)
            py5.box(80)
        ```

        As this is creating a DXF file, your code will be limited to the
        capabilities of that renderer.

        Code used in this cell can reference functions and variables defined in
        other cells. By default, variables and functions created in this cell
        will be local to only this cell because to do otherwise would be unsafe.
        If you understand the risks, you can use the `global` keyword to add a
        single function or variable to the notebook namespace or the --unsafe
        argument to add everything to the notebook namespace. Either option may
        be very useful to you, but be aware that using py5 objects in a
        different notebook cell or reusing them in another sketch can result in
        nasty errors and bizzare consequences. Any and all problems resulting
        from using these features are solely your responsibility and not the py5
        library maintainers.
        """
        args = parse_argstring(self.py5drawdxf, line)
        dxf = run_single_frame_sketch('DXF', cell, args.width, args.height,
                                      self.shell.user_ns, not args.unsafe)
        if dxf:
            filename = self._filename_check(args.filename)
            with open(filename, 'w') as f:
                f.write(dxf)
            print(f'DXF written to {filename}')

    @magic_arguments()
    @argument('width', type=int, help='width of SVG drawing')
    @argument('height', type=int, help='height of SVG drawing')
    @argument('-f', '--filename', type=str, dest='filename', help='save SVG drawing to file')
    @argument('--unsafe', dest='unsafe', action='store_true',
              help="allow new variables to enter the global namespace, creating a potentially unsafe situation")
    @cell_magic
    def py5drawsvg(self, line, cell):
        """Create a SVG drawing with py5 and embed result in the notebook.

        For users who are familiar with Processing and py5 programming, you can
        pretend the code in this cell will be executed in a sketch with no
        `draw()` function and your code in the `setup()` function. It will use
        the SVG renderer.

        The below example will create a red square on a gray background:

        ```
            %%py5drawsvg 500 250
            py5.background(128)
            py5.fill(255, 0, 0)
            py5.rect(80, 100, 50, 50)
        ```

        As this is creating a SVG drawing, you cannot do operations on the
        `pixels` or `np_pixels` arrays. Use `%%py5draw` instead.

        Code used in this cell can reference functions and variables defined in
        other cells. By default, variables and functions created in this cell
        will be local to only this cell because to do otherwise would be unsafe.
        If you understand the risks, you can use the `global` keyword to add a
        single function or variable to the notebook namespace or the --unsafe
        argument to add everything to the notebook namespace. Either option may
        be very useful to you, but be aware that using py5 objects in a
        different notebook cell or reusing them in another sketch can result in
        nasty errors and bizzare consequences. Any and all problems resulting
        from using these features are solely your responsibility and not the py5
        library maintainers.
        """
        args = parse_argstring(self.py5drawsvg, line)
        svg = run_single_frame_sketch('SVG', cell, args.width, args.height,
                                      self.shell.user_ns, not args.unsafe)
        if svg:
            if args.filename:
                filename = self._filename_check(args.filename)
                with open(filename, 'w') as f:
                    f.write(svg)
                print(f'SVG drawing written to {filename}')
            display(SVG(svg))

    @magic_arguments()
    @argument('width', type=int, help='width of PNG image')
    @argument('height', type=int, help='height of PNG image')
    @argument('-f', '--filename', dest='filename', help='save image to file')
    @argument('-r', '--renderer', type=str, dest='renderer', default='HIDDEN',
              help='processing renderer to use for sketch')
    @argument('--unsafe', dest='unsafe', action='store_true',
              help="allow new variables to enter the global namespace, creating a potentially unsafe situation")
    @cell_magic
    def py5draw(self, line, cell):
        """Create a PNG image with py5 and embed result in the notebook.

        For users who are familiar with Processing and py5 programming, you can
        pretend the code in this cell will be executed in a sketch with no
        `draw()` function and your code in the `setup()` function. By default it
        will use the default Processing renderer.

        The below example will create a red square on a gray background:

        ```
            %%py5draw 500 250
            py5.background(128)
            py5.fill(255, 0, 0)
            py5.rect(80, 100, 50, 50)
        ```

        Code used in this cell can reference functions and variables defined in
        other cells. By default, variables and functions created in this cell
        will be local to only this cell because to do otherwise would be unsafe.
        If you understand the risks, you can use the `global` keyword to add a
        single function or variable to the notebook namespace or the --unsafe
        argument to add everything to the notebook namespace. Either option may
        be very useful to you, but be aware that using py5 objects in a
        different notebook cell or reusing them in another sketch can result in
        nasty errors and bizzare consequences. Any and all problems resulting
        from using these features are solely your responsibility and not the py5
        library maintainers.
        """
        args = parse_argstring(self.py5draw, line)

        if args.renderer == 'SVG':
            print('please use %%py5drawsvg for SVG drawings.')
            return
        if args.renderer == 'PDF':
            print('please use %%py5drawpdf for PDFs.')
            return
        if args.renderer not in ['HIDDEN', 'JAVA2D', 'P2D', 'P3D']:
            print(f'unknown renderer {args.renderer}')
            return

        png = run_single_frame_sketch(args.renderer, cell, args.width, args.height,
                                      self.shell.user_ns, not args.unsafe)
        if png:
            if args.filename:
                filename = self._filename_check(args.filename)
                PIL.Image.open(io.BytesIO(png)).convert(mode='RGB').save(filename)
                print(f'PNG file written to {filename}')
            display(Image(png))

    @line_magic
    @magic_arguments()
    @argument('-w', type=int, dest='wait', default=0, help='wait time in seconds before taking screenshot')
    def py5screenshot(self, line):
        """Take a screenshot of the current running sketch.

        Use the -w argument to wait before taking the screenshot.

        The returned image is a `PIL.Image` object. It can be assigned to a
        variable or embedded in the notebook.

        Below is an example demonstrating how to take a screenshot after a two
        second delay and assign it to the `img` variable. The image is then
        saved to a file. When run from a notebook, the image is embedded in the
        output.

        ```
            img = %py5screenshot -w 2
            img.save('image.png')
            img
        ```
        """
        args = parse_argstring(self.py5screenshot, line)
        import py5
        sketch = py5.get_current_sketch()

        if not sketch.is_running:
            print('The current sketch is not running.')
            return

        wait(args.wait, sketch)

        with tempfile.NamedTemporaryFile(suffix='.png') as png_file:
            hook = ScreenshotHook(png_file.name)
            sketch._add_post_hook('draw', hook.hook_name, hook)

            while not hook.is_ready and not hook.is_terminated:
                time.sleep(0.005)

            if hook.is_ready:
                return PIL.Image.open(png_file.name)
            elif hook.is_terminated and hook.exception:
                print('error running magic:', hook.exception)

    @line_magic
    @magic_arguments()
    @argument('dirname', type=str, help='directory to save the frames')
    @argument('--filename', type=str, dest='filename', default='frame_####.png',
              help='filename to save frames to')
    @argument('-w', type=int, dest='wait', default=0,
              help='wait time in seconds before starting sketch frame capture')
    @argument('-s', dest='start', type=int,
              help='frame starting number instead of sketch frame_count')
    @argument('--limit', type=int, dest='limit', default=0,
              help='limit the number of frames to save (default 0 means no limit)')
    def py5screencapture(self, line):
        """Save the current running sketch's frames to a directory.

        Use the -w argument to wait before starting.

        The below example will save the next 50 frames to the `/tmp/frames`
        directory after a 3 second delay. The filenames will be saved with the
        default name 'frame_####.png' with numbering that starts at 0.

        ```
            %py5screencapture /tmp/frames -w 3 -s 0 --limit 50
        ```

        If a limit is given, this line magic will wait to return a list of the
        filenames. Otherwise, it will return right away as the frames are saved
        in the background. It will keep doing so as long as the sketch continues
        to run.
        """
        args = parse_argstring(self.py5screencapture, line)
        import py5
        sketch = py5.get_current_sketch()

        if not sketch.is_running:
            print('The current sketch is not running.')
            return

        dirname = Path(args.dirname)
        if not dirname.exists():
            dirname.mkdir(parents=True)
        print(f'writing frames to {str(args.dirname)}...')

        wait(args.wait, sketch)

        hook = SaveFramesHook(dirname, args.filename, args.start, args.limit)
        sketch._add_post_hook('draw', hook.hook_name, hook)

        if args.limit:
            while not hook.is_ready and not hook.is_terminated:
                time.sleep(0.02)
                print(f'saving frame {len(hook.filenames)}/{args.limit}', end='\r')
            print('')

            if hook.is_ready:
                return hook.filenames

        if hook.is_terminated and hook.exception:
            print('error running magic:', hook.exception)

    @line_magic
    @magic_arguments()
    @argument('filename', type=str, help='filename of gif to create')
    @argument('count', type=int, help='number of Sketch snapshots to create')
    @argument('delay', type=int, help='time in milliseconds between Sketch snapshots')
    @argument('duration', type=int, help='time in milliseconds between frames in the GIF')
    @argument('-w', type=int, dest='wait', default=0,
              help='wait time in seconds before starting sketch frame capture')
    @argument('-l', dest='loop', type=int, default=0,
              help='number of times for the GIF to loop (default of 0 loops indefinitely')
    @argument('--optimize', action='store_true', help='optimize GIF palette')
    def py5animatedgif(self, line):
        """Save the current running sketch's frames to a directory.

        Use the -w argument to wait before starting.

        The below example will create a 10 frame animated GIF saved to
        '/tmp/animated.gif'. The frames will be recorded 1000 milliseconds
        apart after waiting 3 seconds. The animated GIF will display the frames
        with a 500 millisecond delay between each one and will loop indefinitely.

        ```
            %py5screencapture /tmp/animated.gif 10 1000 500 -w 3
        ```
        """
        args = parse_argstring(self.py5animatedgif, line)
        import py5
        sketch = py5.get_current_sketch()

        if not sketch.is_running:
            print('The current sketch is not running.')
            return

        filename = Path(args.filename)

        wait(args.wait, sketch)

        hook = GrabFramesHook(args.delay, args.count)
        sketch._add_post_hook('draw', hook.hook_name, hook)

        while not hook.is_ready and not hook.is_terminated:
            time.sleep(0.05)
            print(f'collecting frame {len(hook.frames)}/{args.count}', end='\r')
        print('')

        if hook.is_ready:
            if not filename.parent.exists():
                filename.parent.mkdir(parents=True)

            img1 = PIL.Image.fromarray(hook.frames[0], mode='RGB')
            imgs = [PIL.Image.fromarray(arr, mode='RGB') for arr in hook.frames[1:]]
            img1.save(filename, save_all=True, duration=args.duration,
                      loop=args.loop, optimize=args.optimize, append_images=imgs)

            return str(filename)

        elif hook.is_terminated and hook.exception:
            print('error running magic:', hook.exception)


def load_ipython_extension(ipython):
    ipython.register_magics(Py5Magics)
