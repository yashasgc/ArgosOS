#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
media_dir="$repo_root/docs/media"
frame_root="$media_dir/frames"
font_regular="Helvetica"
font_bold="Helvetica-Bold"

mkdir -p "$media_dir" "$frame_root/mcp" "$frame_root/email"

make_slide() {
  output="$1"
  eyebrow="$2"
  title="$3"
  body="$4"
  footer="$5"
  accent="$6"

  magick -size 1280x720 canvas:'#f8fafc' \
    -fill '#ffffff' -stroke '#dbe5f1' -strokewidth 2 \
    -draw 'roundrectangle 54,46 1226,674 28,28' \
    -fill "$accent" -stroke none -draw 'roundrectangle 54,46 72,674 9,9' \
    -font "$font_bold" -fill "$accent" -pointsize 25 -annotate +110+105 "$eyebrow" \
    -font "$font_bold" -fill '#0f172a' -pointsize 52 -annotate +110+185 "$title" \
    -font "$font_regular" -fill '#334155' -pointsize 29 -interline-spacing 14 \
    -annotate +110+285 "$body" \
    -fill '#eef4ff' -stroke none -draw 'roundrectangle 104,602 1180,642 12,12' \
    -font "$font_bold" -fill '#334155' -pointsize 19 -gravity southwest \
    -annotate +124+91 "$footer" \
    -gravity northwest "$output"
}

make_slide \
  "$frame_root/mcp/01.png" \
  'ARGOSOS MCP' \
  'Your document library becomes a tool' \
  $'Connect an AI assistant to the knowledge already stored\non your computer—without creating a separate cloud database.' \
  'Local MCP server · stdio transport · no delete tool' \
  '#2563eb'

make_slide \
  "$frame_root/mcp/02.png" \
  'DISCOVER' \
  'Find the right document' \
  $'argos_list_documents    Browse recent files and metadata\nargos_search_documents  Search titles, summaries, and tags\nargos_list_tags         Discover the local vocabulary' \
  'Read-only tools make exploration safe by default.' \
  '#4f46e5'

make_slide \
  "$frame_root/mcp/03.png" \
  'READ' \
  'Bring evidence into the conversation' \
  $'argos_get_document_text(document_id)\n\nExtracts local text only after validating that the stored file\nis inside the ArgosOS data directory.' \
  'Bounded output prevents accidental oversized responses.' \
  '#0891b2'

make_slide \
  "$frame_root/mcp/04.png" \
  'SAFE BY DEFAULT' \
  'Useful tools, narrow permissions' \
  $'✓ No MCP delete operation\n✓ No arbitrary file-path access\n✓ No secrets returned by status tools\n✓ The same validation serves MCP, HTTP, and future automation' \
  'Next: cited answers and local semantic search.' \
  '#16a34a'

make_slide \
  "$frame_root/email/01.png" \
  'ARGOSOS EMAIL' \
  'Email becomes searchable knowledge' \
  $'Mailbox  →  Safe preview  →  Import  →  OCR and indexing\n\nBodies and supported attachments join the same local library\nas PDFs, scans, notes, and Word documents.' \
  'Generic IMAP today · OAuth adapters can plug in later' \
  '#2563eb'

make_slide \
  "$frame_root/email/02.png" \
  'PREVIEW' \
  'Look before importing' \
  $'argos_email_status   Confirms configuration without a password\nargos_email_preview  Shows sender, subject, date, and attachments\n\nIMAP BODY.PEEK keeps unread messages unread.' \
  'Defaults: unread only · last 30 days · maximum 20 messages' \
  '#7c3aed'

make_slide \
  "$frame_root/email/03.png" \
  'SYNC' \
  'Import once, then keep it local' \
  $'Email body         → searchable text document\nPDF or image       → extraction and OCR\nSupported attachment → normal ArgosOS ingestion\nContent hash       → duplicate protection' \
  'Messages are not marked read unless mark_seen=true.' \
  '#0891b2'

make_slide \
  "$frame_root/email/04.png" \
  'PRIVACY CONTROLS' \
  'Credentials stay out of results' \
  $'✓ Passwords come from environment configuration\n✓ Status APIs report only whether a password exists\n✓ No outbound email or reply tool\n✓ No mailbox deletion or message-moving operation' \
  'Use an app password now; add Gmail and Microsoft OAuth next.' \
  '#16a34a'

render_video() {
  name="$1"
  frames="$2"
  concat_file="/tmp/$name-concat.txt"
  : > "$concat_file"
  for frame in "$frames"/*.png; do
    printf "file '%s'\nduration 3\n" "$frame" >> "$concat_file"
  done
  last_frame="$(find "$frames" -name '*.png' -type f | sort | tail -1)"
  printf "file '%s'\n" "$last_frame" >> "$concat_file"

  ffmpeg -hide_banner -loglevel error -y \
    -f concat -safe 0 -i "$concat_file" \
    -vf 'fps=30,format=yuv420p' -an -map_metadata -1 \
    -c:v libx264 -preset medium -crf 22 -movflags +faststart \
    "$media_dir/$name.mp4"

  magick -delay 300 -loop 0 "$frames"/*.png \
    -resize 960x540 -layers Optimize "$media_dir/$name-preview.gif"
}

render_video 'argos-mcp-tools' "$frame_root/mcp"
render_video 'argos-email-ingestion' "$frame_root/email"

echo "Created demo media in $media_dir"
