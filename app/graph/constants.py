# app/graph/constants.py
"""
Small shared constants used by more than one graph node.

FIX (weak point #19): the "More Options" pagination sentinel needs to be
recognized identically by both memory_node (which must NOT try to extract a
profile field out of it) and writer_node (which builds the list rows that
contain it) -- defining it once here avoids the two nodes drifting out of
sync with each other.
"""

MORE_OPTIONS_ID = "__MORE_OPTIONS__"
MORE_OPTIONS_TITLE = "➡️ More Options"

PAGE_SIZE = 9  # 9 real rows + 1 "More Options" row = WhatsApp's 10-row cap
