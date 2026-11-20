"""Build docs/SkyCrawler_parts_and_links.xlsx (same layout as the Bean-to-Cup list):
sheet 'Parts' = everything to buy, with links and prices; sheet 'Printed parts' = every STL."""
import os, json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.comments import Comment

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'docs', 'SkyCrawler_parts_and_links.xlsx')
GH = 'https://github.com/vishu-aggarwal-001/tvc-rocket/blob/main/stl/'
AMZ = 'https://www.amazon.com/s?k='

# part, link, qty, each, store, cheaper text, cheaper link, stage, notes
BUY = [
 ('MG90S metal-gear micro servo, 10-pack', AMZ + 'MG90S+metal+gear+servo+10+pack', 1, 22, 'Amazon (search)',
  'eBay 10-pack MG90S $19.95', 'https://www.ebay.com/itm/334694718079', 'Robot (walking)',
  'Need 8 (4 hips, 4 knees), so 2 spares. Comes with cross horns and screws. Typical price.'),
 ('ESP32-S3 SuperMini, 3-pack', 'https://www.amazon.com/dp/B0F8845S9P', 1, 18.99, 'Amazon', None, None, 'Robot (walking)',
  'The robot\'s brain. Get the 4 MB flash version (the firmware is built for 4 MB). Price last seen Aug 2025; confirm at checkout.'),
 ('Matek BEC12S-Pro, 5 A buck regulator (5.2 V)', 'https://www.racedayquads.com/products/matek-bec12s-pro-9-55v-to-5-8-12v-5a', 1, 18.99,
  'RaceDayQuads', None, None, 'Robot (walking)',
  'Powers the 8 servos and the ESP32 from the 3S battery. Never run the servos from the flight controller\'s 5 V.'),
 ('Resistor kit (uses 100 kΩ + 22 kΩ)', AMZ + 'resistor+assortment+kit', 1, 8, 'Amazon (search)', None, None, 'Robot (walking)',
  'Battery-voltage divider into GPIO1. Typical price.'),
 ('Active buzzer 5 V (pack)', AMZ + 'active+buzzer+5V', 1, 6, 'Amazon (search)', None, None, 'Robot (walking)',
  'Optional: beeps on start-up and when the drone mode is ready. Typical price.'),
 ('Perfboard + 2.54 mm male header strips', AMZ + 'perfboard+male+header+2.54', 1, 9, 'Amazon (search)', None, None, 'Robot (walking)',
  'Servo power bus: 8 servo plugs share 5 V and GND. Typical price.'),
 ('USB-C data cable', AMZ + 'usb+c+data+cable', 1, 7, 'Amazon (search)', None, None, 'Robot (walking)',
  'For flashing the ESP32 and setting up Betaflight. Skip if you have one.'),
 ('BETAFPV F4 2-3S 20A AIO flight controller V1', 'https://betafpv.com/products/f4-2-3s-20a-aio-fc-v1', 1, 54.99, 'BETAFPV',
  None, None, 'Drone (flying)',
  'Flight controller + 4-in-1 ESC in one board. 26x26 mm mount (the deck has 26x26 and 20x20 standoffs). Its built-in ELRS receiver goes unused: wire the ESP32 to a free UART (docs/betaflight.md). RaceDayQuads sells it too, $65.99.'),
 ('T-Motor F1204 5000KV motor', 'https://www.racedayquads.com/products/t-motor-f1204-5000kv-motor', 4, 15.99, 'RaceDayQuads',
  'BETAFPV 1204 5000KV, 4-pack $52.99 (sold out when checked)', 'https://betafpv.com/products/1204-5000kv-brushless-motors',
  'Drone (flying)', 'Rated 2-3S, 1.5 mm shaft. Pick 5000KV, not 6500KV. Was pre-order when checked. The arm\'s slotted mount fits any 1103-1404 pattern.'),
 ('Gemfan Hurricane 2520 tri-blade 2.5" props, 1.5 mm, 8-pack', 'https://pyrodrone.com/collections/all-props/2-5', 2, 4.99, 'Pyrodrone',
  'Gemfan 2512 tri-blade 8-pack $3.69', 'https://www.racedayquads.com/collections/all/products/gemfan-hurricane-2512-tri-blade-2-5-prop-8-pack-choose-your-color',
  'Drone (flying)', '4 CW + 4 CCW per pack. Props break, so get spares. The 2512 is cheaper but has less pitch (less thrust).'),
 ('GNB 3S 450 mAh 80C LiPo, XT30', 'https://pyrodrone.com/collections/all-products/products/gnb-3s-11-1v-hv-450mah-lipo-battery-80c-xt30', 2, 14.99,
  'Pyrodrone', 'CNHL MiniStar 3S 450 mAh 70C $13.99', 'https://www.racedayquads.com/collections/all/products/cnhl-450mah-3s-70c-11-1v-li-po-fpv-battery-for-2-and-3-quads-xt30',
  'Drone (flying)', '64 x 18 x 20 mm, 42 g, straps under the belly. Batteries ship by ground only.'),
 ('XT30 connector pairs', AMZ + 'XT30+connector+pairs', 1, 8, 'Amazon (search)', None, None, 'Drone (flying)',
  'Y-split the battery lead to the flight controller and the BEC. Typical price.'),
 ('Silicone wire, 22 AWG + 26 AWG', AMZ + 'silicone+wire+22awg+26awg+kit', 1, 12, 'Amazon (search)', None, None, 'Drone (flying)', 'Typical price.'),
 ('6 x 3 mm N52 neodymium magnets', AMZ + '6x3mm+neodymium+magnets', 1, 9, 'Amazon (search)', None, None, 'Frame hardware',
  'Need 8: a pair per knee end stop. Check the polarity before gluing. Typical price for 50.'),
 ('M2 screw + nut assortment (M2x6, M2x8)', AMZ + 'M2+screw+assortment', 1, 10, 'Amazon (search)', None, None, 'Frame hardware',
  'Motors, horns, flight controller, canopy (4x M2x8). Typical price.'),
 ('M3 heat-set inserts + M3 screws', AMZ + 'M3+heat+set+inserts+screws+kit', 1, 12, 'Amazon (search)', None, None, 'Frame hardware',
  '4 inserts in the pillars + M3x6 for the deck; 4x M3x10 as knee levelling screws. Typical price.'),
 ('Battery strap 10 x 130 mm, non-slip', AMZ + 'lipo+battery+strap+10x130', 1, 6, 'Amazon (search)', None, None, 'Frame hardware', 'Typical price.'),
 ('Small zip ties (2.5 mm)', AMZ + 'small+zip+ties+2.5mm', 1, 5, 'Amazon (search)', None, None, 'Frame hardware', 'ESP32 and wiring. Typical price.'),
 ('M2 soft-mount grommets', AMZ + 'M2+flight+controller+soft+mount+grommets', 1, 6, 'Amazon (search)', None, None, 'Frame hardware',
  'Optional: isolates the flight controller from servo vibration. Typical price.'),
 ('PETG filament, 1 kg', AMZ + 'Bambu+PETG+HF+1kg', 1, 22.99, 'Amazon (search)', None, None, '3D printing',
  'About 90 g for one robot (see the Printed parts tab). Your Bean-to-Cup list already has Bambu PETG HF; any colour, white canopy looks best.'),
 ('Bambu TPU 95A HF, 1 kg', 'https://us.store.bambulab.com/collections/tpu', 1, 41.99, 'Bambu Lab US store',
  'Any TPU 95A, small spool', AMZ + 'TPU+95A+filament+250g', '3D printing',
  'Only the 4 feet (about 4 g). Was on sale at $37.79 when checked. Dry it before printing.'),
 ('ToolkitRC M6AC LiPo balance charger', 'https://www.racedayquads.com/products/toolkitrc-m6ac-300w-15a-1-6s-ac-charger-xt60', 1, 71.99,
  'RaceDayQuads', 'ImexRC $59.99 (backordered when checked)', 'https://www.imexrc.com/products/toolkitrc-m6ac-smart-charger-dual-input-300w-rc-battery-charger-with-usb-c-output',
  'Tools', 'Charges from a wall socket. Never charge a LiPo unattended.'),
 ('XT60 to XT30 charge adapter', AMZ + 'XT60+to+XT30+adapter', 1, 6, 'Amazon (search)', None, None, 'Tools', 'The charger is XT60, the battery is XT30. Typical price.'),
 ('LiPo safe bag', AMZ + 'lipo+safe+bag', 1, 10, 'Amazon (search)', None, None, 'Tools', 'Charge and store batteries in it. Typical price.'),
 ('Soldering iron (Pinecil) + heat-set insert tip', AMZ + 'Pinecil+soldering+iron', 1, 30, 'Amazon (search)', None, None, 'Tools',
  'Skip if you have one. Typical price.'),
]

def main():
    parts = json.load(open(os.path.join(ROOT, 'tools', 'printed_parts.json')))
    wb = Workbook(); ws = wb.active; ws.title = 'Parts'
    F = Font(name='Arial', size=10); B = Font(name='Arial', size=10, bold=True)
    HF = PatternFill('solid', fgColor='FFE3F1E9'); WR = Alignment(wrap_text=True, vertical='top'); TOP = Alignment(vertical='top')
    MONEY = '$#,##0.00'
    ws['A1'] = 'Still to buy'; ws['A1'].font = B
    last = 3 + len(BUY)
    ws['B1'] = f'=SUMIFS(E4:E{last},A4:A{last},FALSE)'; ws['B1'].font = B; ws['B1'].number_format = MONEY
    ws['A2'] = 'Without tools'; ws['A2'].font = F
    ws['B2'] = f'=SUMIFS(E4:E{last},A4:A{last},FALSE,H4:H{last},"<>Tools")'; ws['B2'].font = F; ws['B2'].number_format = MONEY
    heads = ['Got it', 'Part (tap to buy)', 'Qty', 'Each', 'Line', 'Store', 'Cheaper option', 'Stage', 'Notes']
    for i, h in enumerate(heads, 1):
        c = ws.cell(3, i, h); c.font = F; c.fill = HF
    for r, (part, link, qty, each, store, ch, chl, stage, note) in enumerate(BUY, 4):
        ws.cell(r, 1, False)
        c = ws.cell(r, 2, part); c.hyperlink = link
        ws.cell(r, 3, qty); ws.cell(r, 4, each).number_format = MONEY
        ws.cell(r, 5, f'=IF(D{r}="","",C{r}*D{r})').number_format = MONEY
        ws.cell(r, 6, store)
        if ch:
            c = ws.cell(r, 7, ch); c.hyperlink = chl
        ws.cell(r, 8, stage); ws.cell(r, 9, note)
        for col in range(1, 10):
            cell = ws.cell(r, col); cell.font = F
            cell.alignment = WR if col in (2, 7, 9) else TOP
    widths = {'A': 12.9, 'B': 42.9, 'C': 4.7, 'D': 10.7, 'E': 10.7, 'F': 33.3, 'G': 31.4, 'H': 18.7, 'I': 45.7}
    for k, v in widths.items():
        ws.column_dimensions[k].width = v
    ws.freeze_panes = 'A4'
    ws['A1'].comment = Comment('Prices checked online in Nov 2026 (USD, before shipping and tax). '
                               '"Typical price" rows link to a search page; the price is an estimate. Tick "Got it" (TRUE) as you buy.', 'SkyCrawler')

    # ---- printed parts
    ps = wb.create_sheet('Printed parts')
    ps['A1'] = 'Still to print'; ps['A1'].font = B
    plast = 3 + len(parts)
    ps['B1'] = f'=SUMIFS(C4:C{plast},A4:A{plast},FALSE)'; ps['B1'].font = B; ps['B1'].number_format = '0" parts"'
    ps['A2'] = 'Filament (g)'; ps['A2'].font = F
    ps['B2'] = f'=SUMPRODUCT(C4:C{plast},G4:G{plast})'; ps['B2'].font = F; ps['B2'].number_format = '0'
    heads = ['Printed', 'Part (tap for 3D view)', 'Qty', 'Material', 'Settings', 'Size (mm)', 'g each', 'STL file', 'What it does']
    for i, h in enumerate(heads, 1):
        c = ps.cell(3, i, h); c.font = F; c.fill = HF
    for r, p in enumerate(parts, 4):
        ps.cell(r, 1, False)
        c = ps.cell(r, 2, p['title']); c.hyperlink = GH + p['file'] + '.stl'
        ps.cell(r, 3, 0 if p['qty'] == '0–4' else int(p['qty']))
        ps.cell(r, 4, p['mat']); ps.cell(r, 5, p['settings'].replace(' · ', ', '))
        ps.cell(r, 6, ' x '.join(f'{d:g}' for d in p['dims'])); ps.cell(r, 7, p['grams'])
        ps.cell(r, 8, p['file'] + '.stl')
        ps.cell(r, 9, p['note'] + (' Print 0-4 as needed.' if p['qty'] == '0–4' else ''))
        for col in range(1, 10):
            cell = ps.cell(r, col); cell.font = F
            cell.alignment = WR if col in (2, 5, 9) else TOP
    for k, v in {'A': 12.9, 'B': 30, 'C': 4.7, 'D': 22, 'E': 34, 'F': 18, 'G': 8, 'H': 18, 'I': 55}.items():
        ps.column_dimensions[k].width = v
    ps.freeze_panes = 'A4'
    ps['A2'].comment = Comment('Rough filament estimate: solid volume x density x 0.55 (walls + infill). '
                               'parts.html in the STL zip shows each part in 3D.', 'SkyCrawler')
    wb.save(OUT); print('wrote', OUT)

if __name__ == '__main__':
    main()
