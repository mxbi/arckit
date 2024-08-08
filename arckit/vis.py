import drawsvg
import numpy as np
import io

cmap = [
    '#252525', # black
    '#0074D9', # blue
    '#FF4136', # red
    '#37D449', #2ECC40', # green
    '#FFDC00', # yellow
    '#E6E6E6', # grey
    '#F012BE', # pink
    '#FF871E', # orange
    '#54D2EB', #7FDBFF', # light blue
    '#8D1D2C',#870C25', # brown
    '#FFFFFF'
        ]

def draw_grid(grid, xmax=10, ymax=10, padding=.5, extra_bottom_padding=0.5, group=False, add_size=True, label='', bordercol='#111111ff'):
    """
    Draws a grid, 

    Parameters
    ----------
    grid : np.ndarray
        The grid to draw
    xmax : float, optional
        The maximum horizontal size of the drawing, by default 10
    ymax : float, optional
        The maximum vertical size of the drawing, by default 10
    padding : float, optional
        The padding around the grid, half on each side, by default .5
    extra_bottom_padding : float, optional
        Extra padding at the bottom of the drawing, by default 0.5
        This is used to draw the label
    group : bool, optional
        If enabled, return a drawsvg.Group to include within a bigger drawing
        Otherwise, return a drawsvg.Drawing (default)
    label : str, optional
        A label to draw at the bottom left of the drawing, by default ''
        This does not affect drawing of the size.
    bordercol : str, optional
        The colour of the border, by default '#111111ff'
    """
    # Size is the total size of the LARGER axis.
    # With 0.5 cell padding, we consider the grid to be 1 unit larger than the number of cells
    # padding *= size # padding is proportional
    
    gridy, gridx = grid.shape
    # Calculate cell size based on the two restrictions
    # The actual cell size is the minimum of the two
    cellsize_x = xmax / gridx
    cellsize_y = ymax / gridy
    cellsize = min(cellsize_x, cellsize_y)

    xsize = gridx * cellsize
    ysize = gridy * cellsize

    line_thickness = 0.01
    circle_radius = 0
    border_width = 0.08
    lt = line_thickness / 2

    if group:
        drawing = drawsvg.Group()
    else:
        drawing = drawsvg.Drawing(xsize+padding, ysize+padding+extra_bottom_padding, origin=(-0.5*padding, -0.5*padding))
        drawing.set_pixel_scale(40)
    # drawing = drawsvg.Group()
    for j, row in enumerate(grid):
        for i, cell in enumerate(row):
            drawing.append(drawsvg.Rectangle(i*cellsize+lt, j*cellsize+lt, cellsize-lt, cellsize-lt, fill=cmap[cell]))
    
    # white dot at each vertex
    if circle_radius > 0:
        for i in range(1, gridx):
            for j in range(1, gridy):
                drawing.append(drawsvg.Circle(i*cellsize, j*cellsize, circle_radius, fill='white'))
        
    # Add a border
    bw = border_width / 3 # slightly more than 2 to avoid white border
    drawing.append(drawsvg.Rectangle(-bw, -bw, xsize+bw*2, ysize+bw*2, fill='none', stroke=bordercol, stroke_width=border_width))

    if not group:
        drawing.embed_google_font('Anuphan:wght@400;600;700', text=set(f'Input Output 0123456789x Test Task ABCDEFGHIJ? abcdefghjklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ'))

    # Write size on the bottom right
    # drawing.append(drawsvg.Text(text=f'{gridx}x{gridy}', x=-0.05, y=-0.25, font_size=padding/4, fill='black', text_anchor='start'))
    fontsize = (padding/2 + extra_bottom_padding)/2
    if add_size:
        drawing.append(drawsvg.Text(text=f'{gridx}x{gridy}', x=xsize, y=ysize+fontsize*1.25+0, font_size=fontsize, fill='black', text_anchor='end', font_family='Anuphan'))
    if label:
        drawing.append(drawsvg.Text(text=label, x=-0.1*fontsize, y=ysize+fontsize*1.25+0, font_size=fontsize, fill='black', text_anchor='start', font_family='Anuphan', font_weight='600'))
    
    if group:
        # return group, origin, (xsize, ysize)
        return drawing, (-0.5*padding, -0.5*padding), (xsize+padding, ysize+padding+extra_bottom_padding)
    return drawing

def draw_task(task, width=30, height=12, include_test=False, label=True, bordercols=['#111111ff', '#111111ff'], shortdesc=False):
    """
    Plot an entire task vertically, fitting the desired dimensions.
    The output is displayed below the input, with an arrow in between.

    Note that dimensions are a best effort, you should check .width and .height on the output
    
    Parameters
    ----------
    task : Task
        The task to plot
    width : float, optional
        The desired width of the drawing, by default 30
    height : float, optional
        The desired height of the drawing, by default 12
    include_test : bool, optional
        If enabled, include the test examples in the plot, by default False
        If set to 'all', ALSO include the output of the test examples
    label: bool, default True
    bordercols: list of str, default None
    """

    padding = 0.5
    bonus_padding = 0.25
    io_gap = 0.4
    ymax = (height - padding - bonus_padding - io_gap)/2

    if include_test:
        examples = task.train + task.test
    else:
        examples = task.train
    n_train = len(task.train)
    paddingless_width = width - padding * len(examples)

    max_widths = np.zeros(len(examples))
    # If any examples would exceed the height restriction, scale their width down and redistribute the space
    for i, (input_grid, output_grid) in enumerate(examples):
        input_grid_ratio = input_grid.shape[1] / input_grid.shape[0]
        output_grid_ratio = output_grid.shape[1] / output_grid.shape[0]
        max_ratio = max(input_grid_ratio, output_grid_ratio) # could be min
        xmax = ymax * max_ratio
        max_widths[i] = xmax

    # Allocate paddingless width to each example
    allocation = np.zeros_like(max_widths)
    increment = 0.01
    for i in range(int(paddingless_width//increment)):
        incr = (allocation + increment) <= max_widths
        allocation[incr] += increment / incr.sum()

    drawlist = []
    x_ptr = 0
    y_ptr = 0
    for i, (input_grid, output_grid) in enumerate(examples):
        if shortdesc:
            if i >= n_train:
                input_label = ''#f'T{i-n_train+1}'
                output_label = ''#f'T{i-n_train+1}'
            else:
                input_label = ''#f'I{i+1}'
                output_label = ''#f'O{i+1}'
        else:
            if i >= n_train:
                input_label = f'Test {i-n_train+1}'
                output_label = f'Test {i-n_train+1}'
            else:
                input_label = f'Input {i+1}'
                output_label = f'Output {i+1}'

        # input_label, output_label = '', ''

        input_grid, offset, (input_x, input_y) = draw_grid(input_grid, padding=padding, xmax=allocation[i], ymax=ymax, group=True, label=input_label, extra_bottom_padding=0.5, bordercol=bordercols[0])
        output_grid, offset, (output_x, output_y) = draw_grid(output_grid, padding=padding, xmax=allocation[i], ymax=ymax, group=True, label=output_label, extra_bottom_padding=0.5, bordercol=bordercols[1])

        drawlist.append(drawsvg.Use(input_grid, x=x_ptr + (allocation[i]+padding-input_x)/2 - offset[0], y=-offset[1]))
        # drawlist.append(drawsvg.Use(output_grid, x=x_ptr + (allocation[i]+padding-output_x)/2 - offset[0], y=ymax-offset[1]+2))
        x_ptr += max(input_x, output_x)
        y_ptr = max(y_ptr, input_y)

    x_ptr = 0
    y_ptr2 = 0
    for i, (input_grid, output_grid) in enumerate(examples):
        if shortdesc:
            if i >= n_train:
                input_label = ''#f'T{i-n_train+1}'
                output_label = ''#f'T{i-n_train+1}'
            else:
                input_label = ''#f'I{i+1}'
                output_label = ''#f'O{i+1}'
        else:
            if i >= n_train:
                input_label = f'Test {i-n_train+1}'
                output_label = f'Test {i-n_train+1}'
            else:
                input_label = f'Input {i+1}'
                output_label = f'Output {i+1}'
        # input_label, output_label = '', ''

        input_grid, offset, (input_x, input_y) = draw_grid(input_grid, padding=padding, xmax=allocation[i], ymax=ymax, group=True, label=input_label, extra_bottom_padding=0.5, bordercol=bordercols[0])
        output_grid, offset, (output_x, output_y) = draw_grid(output_grid, padding=padding, xmax=allocation[i], ymax=ymax, group=True, label=output_label, extra_bottom_padding=0.5, bordercol=bordercols[1])
                # Down arrow
        drawlist.append(drawsvg.Line(
            x_ptr + input_x/2, 
            y_ptr + padding - 0.6, 
            x_ptr + input_x/2, 
            y_ptr + padding + io_gap - 0.6, 
            stroke_width=0.05, stroke='#888888'))
        drawlist.append(drawsvg.Line(
            x_ptr + input_x/2 - 0.15,
            y_ptr + padding + io_gap - 0.8,
            x_ptr + input_x/2,
            y_ptr + padding + io_gap - 0.6,
            stroke_width=0.05, stroke='#888888'))
        drawlist.append(drawsvg.Line(
            x_ptr + input_x/2 + 0.15,
            y_ptr + padding + io_gap - 0.8,
            x_ptr + input_x/2,
            y_ptr + padding + io_gap - 0.6,
            stroke_width=0.05, stroke='#888888'))
        

        if i < n_train or include_test == 'all':
            drawlist.append(drawsvg.Use(output_grid, x=x_ptr + (allocation[i]+padding-output_x)/2 - offset[0], y=y_ptr-offset[1]+io_gap))
        else:
            # Add a question mark
            drawlist.append(drawsvg.Text(
                '?',
                x=x_ptr + (allocation[i]+padding)/2,
                y=y_ptr + output_y/2+bonus_padding,
                font_size=1,
                font_family='Anuphan',
                font_weight='700',
                fill='#333333',
                text_anchor='middle',
                alignment_baseline='middle',
            ))
        x_ptr += max(input_x, output_x)
        y_ptr2 = max(y_ptr2, y_ptr+output_y+io_gap)

    x_ptr = round(x_ptr, 1)
    y_ptr2 = round(y_ptr2, 1)
    d = drawsvg.Drawing(x_ptr, y_ptr2+0.2, origin=(0, 0))
    d.append(drawsvg.Rectangle(0, 0, '100%', '100%', fill='#eeeff6'))
    d.embed_google_font('Anuphan:wght@400;600;700', text=set(f'Input Output 0123456789x Test Task ABCDEFGHIJ? abcdefghjklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    for item in drawlist:
        d.append(item)

    fontsize=0.3
    d.append(drawsvg.Text(f"Task {task.id}", x=x_ptr-0.1, y=y_ptr2+0.1, font_size=fontsize, font_family='Anuphan', font_weight='600', fill='#666666', text_anchor='end', alignment_baseline='bottom'))

    d.set_pixel_scale(40)
    return d

def output_drawing(d: drawsvg.Drawing, filename: str, context=None):
    if filename.endswith('.svg'):
        d.save_svg(filename)
    elif filename.endswith('.png'):
        d.save_png(filename)
    elif filename.endswith('.pdf'):
        buffer = io.StringIO()
        d.as_svg(output_file=buffer, context=context)

        import cairosvg
        cairosvg.svg2pdf(bytestring=buffer.getvalue(), write_to=filename)
    else:
        raise ValueError(f'Unknown file extension for {filename}')