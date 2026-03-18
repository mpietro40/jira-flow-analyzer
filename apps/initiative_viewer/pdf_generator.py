"""
Initiative Viewer PDF Generator
Grid-based PDF report: areas as columns, post-it style epic cells, risk colours.

Author: Pietro Maffi
Version: 3.0.0
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.common import PDFGeneratorBase
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, LongTable, TableStyle, Paragraph, Spacer, PageBreak
)
import math
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from typing import List, Dict, Optional, BinaryIO
from datetime import datetime
import logging

logger = logging.getLogger('InitiativeViewerPDF')

# Page-size constants exported for the routes in app.py
PAGE_A4_LANDSCAPE  = landscape(A4)            # 11.69" × 8.27"  — default PDF
PAGE_A3_LANDSCAPE  = landscape(A3)            # 16.54" × 11.69" — A3 wide
PAGE_SUPER_WIDE    = (20 * inch, 11.69 * inch) # 20"   × 11.69" — super-wide

# Risk background colours (post-it cells)
_RISK_BG = {
    1:    colors.HexColor('#c6f6d5'),  # light green  — low risk / committed
    2:    colors.HexColor('#9ae6b4'),  # green        — low-medium
    3:    colors.HexColor('#fefcbf'),  # yellow       — medium
    4:    colors.HexColor('#fbd38d'),  # orange       — medium-high
    5:    colors.HexColor('#fc8181'),  # red          — high risk / out
    6:    colors.HexColor('#e9d8fd'),  # purple       — added during PI
    None: colors.HexColor('#e2e8f0'),  # light grey   — no data
}
_COMPLETED_BG = colors.HexColor('#68d391')  # bright green


class InitiativeViewerPDFGenerator(PDFGeneratorBase):
    """Grid-based PDF generator: Feature/Sub-Feature rows × Area columns."""

    # Max area-columns per table on a non-wide page before splitting
    _MAX_AREAS_A4 = 5

    def __init__(self, jira_base_url: str):
        super().__init__()
        self.jira_base_url = jira_base_url.rstrip('/')

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_hierarchy_pdf(
        self,
        initiatives: List[Dict],
        output_file: BinaryIO,
        fix_version: str,
        page_size=PAGE_A4_LANDSCAPE,
        title: Optional[str] = None,
    ):
        """
        Generate the grid-based PDF.

        page_size values:
            PAGE_A4_LANDSCAPE  (default) — landscape A4,  ~11.7 × 8.3 in
            PAGE_A3_LANDSCAPE            — landscape A3,  ~16.5 × 11.7 in
            PAGE_SUPER_WIDE              — custom wide,   20 × 11.7 in
        """
        # Collect all areas across every initiative for consistent columns
        all_areas = sorted({
            area
            for ini in initiatives
            for feat in ini.get('features', [])
            for sf in feat.get('sub_features', [])
            for area in sf.get('epics_by_area', {})
        })

        is_wide = page_size[0] >= 15 * inch  # A3 landscape or super-wide

        doc = SimpleDocTemplate(
            output_file,
            pagesize=page_size,
            title=title or f"Initiative Hierarchy - {fix_version}",
            author="Pietro Maffi",
            leftMargin=20,
            rightMargin=20,
            topMargin=20,
            bottomMargin=50,
        )

        styles = self._make_styles()
        story  = []

        # Title page
        story.extend(self._title_page(initiatives, fix_version, all_areas, styles))
        story.append(PageBreak())

        # One table per initiative
        for idx, initiative in enumerate(initiatives):
            if not initiative.get('features'):
                continue
            if idx > 0:
                story.append(PageBreak())
            story.extend(
                self._initiative_section(initiative, all_areas, fix_version, is_wide, page_size, styles)
            )

        doc.build(
            story,
            onFirstPage=self._footer,
            onLaterPages=self._footer,
        )
        logger.info(f"✅ PDF generated: {len(initiatives)} initiatives, {len(all_areas)} areas")

    # ── Styles ────────────────────────────────────────────────────────────────

    def _make_styles(self):
        styles = getSampleStyleSheet()

        def add(name, parent='Normal', **kw):
            if name not in styles:
                styles.add(ParagraphStyle(name=name, parent=styles[parent], **kw))

        add('RPTitle',    'Title',   fontSize=24, textColor=colors.HexColor('#667eea'),
                                     spaceAfter=16, alignment=TA_CENTER, fontName='Helvetica-Bold')
        add('RPSubtitle', 'Normal',  fontSize=13, textColor=colors.HexColor('#4a5568'),
                                     spaceAfter=8,  alignment=TA_CENTER, fontName='Helvetica-Bold')
        add('RPInfo',     'Normal',  fontSize=10, textColor=colors.HexColor('#2d3748'),
                                     spaceAfter=6,  fontName='Helvetica')
        add('RPIniHdr',   'Normal',  fontSize=12, textColor=colors.HexColor('#667eea'),
                                     spaceAfter=6,  fontName='Helvetica-Bold')
        add('RPCell',     'Normal',  fontSize=7,  textColor=colors.HexColor('#2d3748'),
                                     fontName='Helvetica', leading=9)
        return styles

    # ── Footer ────────────────────────────────────────────────────────────────

    def _footer(self, canvas, doc):
        canvas.saveState()
        w = doc.pagesize[0]
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#718096'))
        canvas.drawString(30, 18, '© Pietro Maffi — Initiative Hierarchy Report')
        canvas.drawRightString(w - 30, 18, f'Page {canvas.getPageNumber()}')
        canvas.setStrokeColor(colors.HexColor('#e2e8f0'))
        canvas.setLineWidth(0.5)
        canvas.line(30, 32, w - 30, 32)
        canvas.restoreState()

    # ── Title page ────────────────────────────────────────────────────────────

    def _title_page(self, initiatives, fix_version, all_areas, styles):
        elements = [
            Paragraph('Initiative Hierarchy Report', styles['RPTitle']),
            Spacer(1, 0.25 * inch),
        ]

        meta = [
            ['Program Increment / Fix Version', f'<b>{fix_version}</b>'],
            ['Generated', f'<b>{datetime.now().strftime("%B %d, %Y at %H:%M")}</b>'],
            ['Total Initiatives',  f'<b>{len(initiatives)}</b>'],
            ['Initiatives with features',
             f'<b>{sum(1 for i in initiatives if i.get("features"))}</b>'],
            ['Total Areas / Projects', f'<b>{len(all_areas)}</b>'],
        ]
        rows = [[Paragraph(r[0], styles['RPInfo']), Paragraph(r[1], styles['RPInfo'])]
                for r in meta]
        meta_tbl = Table(rows, colWidths=[2.5 * inch, 5 * inch])
        meta_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('BOX',  (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(meta_tbl)
        elements.append(Spacer(1, 0.3 * inch))

        # Legend
        elements.append(Paragraph('<b>Risk / Completion Legend:</b>', styles['RPInfo']))
        elements.append(Spacer(1, 0.05 * inch))
        legend = [
            (colors.HexColor('#68d391'), '✓ Completed'),
            (_RISK_BG[1],    '1 – Low / Committed'),
            (_RISK_BG[2],    '2 – Low-Medium'),
            (_RISK_BG[3],    '3 – Medium / Tentative'),
            (_RISK_BG[4],    '4 – Medium-High'),
            (_RISK_BG[5],    '5 – High / Out'),
            (_RISK_BG[6],    '6 – Added (new PI topic)'),
            (_RISK_BG[None], 'No risk data'),
        ]
        leg_data = [[
            Table([[Paragraph(f'<font size="8">{txt}</font>', styles['RPInfo'])]],
                  colWidths=[1.4 * inch],
                  style=TableStyle([('BACKGROUND', (0,0), (0,0), bg),
                                    ('BOX', (0,0), (0,0), 0.5, colors.HexColor('#718096')),
                                    ('TOPPADDING', (0,0), (0,0), 4),
                                    ('BOTTOMPADDING', (0,0), (0,0), 4),
                                    ('LEFTPADDING', (0,0), (0,0), 6)]))
            for bg, txt in legend
        ]]
        leg_tbl = Table(leg_data, colWidths=[1.5 * inch] * len(legend))
        elements.append(leg_tbl)
        return elements

    # ── Initiative section ────────────────────────────────────────────────────

    def _initiative_section(self, initiative, all_areas, fix_version, is_wide, page_size, styles):
        elements = []
        key  = initiative.get('key', '')
        summ = initiative.get('summary', '')
        comp = initiative.get('completion', {})
        comp_txt = ''
        if comp and comp.get('total', 0) > 0:
            comp_txt = f"  —  {comp['done']}/{comp['total']} epics done ({comp['pct']}%)"

        url = f'{self.jira_base_url}/browse/{key}' if self.jira_base_url else ''
        link = f'<link href="{url}">{key}</link>' if url else key
        elements.append(Paragraph(
            f'<b>{link}</b>: {summ}{comp_txt}', styles['RPIniHdr']
        ))

        # CPO (assignee) line
        cpo = (initiative.get('assignee') or '').strip()
        if cpo and cpo.lower() not in ('unassigned', 'unknown', ''):
            cpo_text = f'\U0001f464 <b>CPO:</b> {cpo}'
        else:
            cpo_text = '\U0001f464 <b>CPO:</b> <i><font color="#a0aec0">N/A</font></i>'
        elements.append(Paragraph(cpo_text, styles['RPInfo']))
        elements.append(Spacer(1, 0.1 * inch))

        # Available printable width (page minus margins)
        avail_w = page_size[0] - 40  # 20pt margin each side

        if is_wide or len(all_areas) <= self._MAX_AREAS_A4:
            elements.extend(self._grid_table(initiative, all_areas, avail_w, is_wide, styles))
        else:
            # Split into chunks for narrow pages
            for i in range(0, len(all_areas), self._MAX_AREAS_A4):
                chunk = all_areas[i:i + self._MAX_AREAS_A4]
                lbl = f'<i>Areas {i+1}–{i+len(chunk)}: {", ".join(chunk)}</i>'
                elements.append(Paragraph(lbl, styles['RPInfo']))
                elements.append(Spacer(1, 0.05 * inch))
                elements.extend(self._grid_table(initiative, chunk, avail_w, is_wide, styles))
                elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _grid_table(self, initiative, areas, avail_w, is_wide, styles):
        """Build one grid table: Feature/Sub-Feature column × area columns."""
        n = len(areas)
        feat_col_w = 2.5 * inch
        area_col_w = (avail_w - feat_col_w) / n if n else avail_w
        col_widths  = [feat_col_w] + [area_col_w] * n

        header = [Paragraph('<b>Feature / Sub-Feature</b>', styles['RPInfo'])]
        header += [Paragraph(f'<b>{a}</b>', styles['RPInfo']) for a in areas]
        table_data    = [header]
        style_cmds = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#667eea')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,0), 9),
            ('ALIGN',      (0,0), (-1,0), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID',   (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',  (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING',    (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,1), (-1,-1), 8),
        ]
        row_idx = 1

        for feature in initiative.get('features', []):
            fk   = feature.get('key', '')
            fsum = feature.get('summary', '')
            furl = f'{self.jira_base_url}/browse/{fk}' if self.jira_base_url else ''
            flink = f'<link href="{furl}">{fk}</link>' if furl else fk
            feat_row = [Paragraph(
                f'<b>🔹 {flink}</b><br/><font size="7">{fsum}</font>',
                styles['RPInfo']
            )] + [''] * n
            table_data.append(feat_row)
            style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#d6e4ff')))
            style_cmds.append(('SPAN',       (0, row_idx), (-1, row_idx)))
            row_idx += 1

            for sf in feature.get('sub_features', []):
                sfk  = sf.get('key', '')
                sfsum = sf.get('summary', '')
                surl  = f'{self.jira_base_url}/browse/{sfk}' if self.jira_base_url else ''
                slink = f'<link href="{surl}">{sfk}</link>' if surl else sfk
                epics_by_area = sf.get('epics_by_area', {})

                # Max epics per cell per row: ~5 keeps row height under page height.
                # All epics are shown via continuation rows.
                chunk_size = 5
                max_epics = max(
                    (len(epics_by_area.get(a, [])) for a in areas), default=0
                )
                num_chunks = max(1, math.ceil(max_epics / chunk_size))

                for chunk_idx in range(num_chunks):
                    start = chunk_idx * chunk_size
                    end   = start + chunk_size

                    if chunk_idx == 0:
                        sf_cell = Paragraph(
                            f'  ↳ <b>{slink}</b><br/><font size="6">  {sfsum}</font>',
                            styles['RPInfo']
                        )
                    else:
                        sf_cell = Paragraph(
                            f'  ↳ <font size="6"><i>{sfk} (cont.)</i></font>',
                            styles['RPInfo']
                        )

                    row = [sf_cell]
                    for area in areas:
                        chunk_epics = epics_by_area.get(area, [])[start:end]
                        if chunk_epics:
                            row.append([self._epic_para(e, is_wide, styles)
                                        for e in chunk_epics])
                        else:
                            row.append('')
                    table_data.append(row)
                    style_cmds.append(('BACKGROUND', (0, row_idx), (0, row_idx),
                                        colors.HexColor('#f7fafc')))
                    row_idx += 1

            # Thick separator after each feature group
            if row_idx > 1:
                style_cmds.append(
                    ('LINEBELOW', (0, row_idx-1), (-1, row_idx-1), 2, colors.HexColor('#667eea'))
                )

        if len(table_data) <= 1:
            return [Paragraph('<i>No features or epics found.</i>', styles['RPInfo'])]

        tbl = LongTable(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle(style_cmds))
        return [tbl, Spacer(1, 0.15 * inch)]

    # ── Epic post-it cell ─────────────────────────────────────────────────────

    def _epic_para(self, epic: Dict, is_wide: bool, styles) -> Paragraph:
        """One coloured post-it paragraph for an epic."""
        key     = epic.get('key', '')
        summary = epic.get('summary', '')
        status  = epic.get('status', '')
        risk    = epic.get('risk_probability')

        # Truncate summary on narrow pages
        max_len = 60 if is_wide else 35
        short   = summary[:max_len] + '…' if len(summary) > max_len else summary

        is_done = status.lower() in {'done', 'closed', 'completed', 'complete',
                                     'resolved', 'prd deployed'}
        bg      = _COMPLETED_BG if is_done else _RISK_BG.get(risk, _RISK_BG[None])
        bg_hex  = '#{:02x}{:02x}{:02x}'.format(
            int(bg.red * 255), int(bg.green * 255), int(bg.blue * 255)
        )
        icon    = '✓' if is_done else '○'

        eurl  = f'{self.jira_base_url}/browse/{key}' if self.jira_base_url else ''
        elink = f'<link href="{eurl}">{key}</link>' if eurl else key

        cell_style = ParagraphStyle(
            f'EC_{key}',
            parent=styles['RPCell'],
            backColor=bg_hex,
            borderColor='#a0aec0',
            borderWidth=0.5,
            borderPadding=3,
            spaceBefore=2,
            spaceAfter=2,
        )
        text = (f'<font size="7"><b>{icon} {elink}</b><br/>'
                f'{short}<br/>'
                f'<font size="5">{status}</font></font>')
        return Paragraph(text, cell_style)
