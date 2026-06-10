from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


OUTPUT_SIZES = {
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
}


def provider_size(aspect_ratio: str, flexible: bool) -> str:
    width, height = OUTPUT_SIZES.get(aspect_ratio, OUTPUT_SIZES["4:5"])
    if flexible:
        return f"{width - width % 16}x{height - height % 16}"
    if width == height:
        return "1024x1024"
    return "1024x1536" if height > width else "1536x1024"


class PosterComposer:
    def compose(self, background: bytes, brief: dict[str, object]) -> tuple[bytes, int, int]:
        target = OUTPUT_SIZES.get(str(brief["aspect_ratio"]), OUTPUT_SIZES["4:5"])
        with Image.open(io.BytesIO(background)) as source:
            image = ImageOps.fit(source.convert("RGB"), target, method=Image.Resampling.LANCZOS)
        overlay = Image.new("RGBA", target, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        width, height = target
        gradient_height = int(height * 0.52)
        for index in range(gradient_height):
            opacity = int(215 * (index / gradient_height) ** 1.7)
            y = height - gradient_height + index
            draw.line((0, y, width, y), fill=(0, 0, 0, opacity))

        margin = int(width * 0.075)
        headline = str(brief["headline"])
        supporting = str(brief.get("supporting_text") or "")
        headline_font = self._fit_font(headline, int(width * 0.092), width - margin * 2, 3)
        supporting_font = self._font(int(width * 0.035), bold=False)
        headline_lines = self._wrap(draw, headline, headline_font, width - margin * 2)
        supporting_lines = self._wrap(draw, supporting, supporting_font, width - margin * 2)
        headline_spacing = int(headline_font.size * 0.24)
        supporting_spacing = int(supporting_font.size * 0.38)
        headline_height = self._text_height(draw, headline_lines, headline_font, headline_spacing)
        supporting_height = (
            self._text_height(draw, supporting_lines, supporting_font, supporting_spacing)
            if supporting_lines
            else 0
        )
        gap = int(height * 0.025) if supporting_lines else 0
        y = height - margin - supporting_height - gap - headline_height
        self._draw_lines(
            draw,
            headline_lines,
            (margin, y),
            headline_font,
            headline_spacing,
            fill="white",
        )
        if supporting_lines:
            self._draw_lines(
                draw,
                supporting_lines,
                (margin, y + headline_height + gap),
                supporting_font,
                supporting_spacing,
                fill=(245, 245, 245, 235),
            )
        composed = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        output = io.BytesIO()
        composed.save(output, format="PNG", optimize=True)
        return output.getvalue(), width, height

    def _fit_font(self, text: str, start_size: int, max_width: int, max_lines: int):
        scratch = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        for size in range(start_size, 31, -2):
            font = self._font(size, bold=True)
            if len(self._wrap(scratch, text, font, max_width)) <= max_lines:
                return font
        return self._font(30, bold=True)

    def _font(self, size: int, bold: bool):
        candidates = [
            Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size=size)
        return ImageFont.load_default(size=size)

    def _wrap(self, draw, text: str, font, max_width: int) -> list[str]:
        if not text.strip():
            return []
        lines: list[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = word
            else:
                for char in word:
                    candidate = current + char
                    if current and draw.textlength(candidate, font=font) > max_width:
                        lines.append(current)
                        current = char
                    else:
                        current = candidate
        if current:
            lines.append(current)
        return lines

    def _text_height(self, draw, lines, font, spacing: int) -> int:
        if not lines:
            return 0
        bbox = draw.textbbox((0, 0), "가Ag", font=font)
        return (bbox[3] - bbox[1]) * len(lines) + spacing * (len(lines) - 1)

    def _draw_lines(self, draw, lines, position, font, spacing: int, fill):
        x, y = position
        bbox = draw.textbbox((0, 0), "가Ag", font=font)
        line_height = bbox[3] - bbox[1]
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill, stroke_width=1, stroke_fill=(0, 0, 0, 45))
            y += line_height + spacing
