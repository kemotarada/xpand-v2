python - <<'PY'
import main as core
import xpand_brand_memory as bm

REFERENCE_ID = 2
NEW_FAMILY = "international_transfer"

with core.db_connect() as conn:
    with conn.cursor() as cur:

        cur.execute(
            """
            UPDATE xpand_visual_references
            SET
                content_family = %s,

                dna_json =
                    COALESCE(dna_json, '{}'::jsonb)
                    ||
                    jsonb_build_object(
                        'content_family',
                        %s,

                        'content_classification',
                        COALESCE(
                            dna_json->'content_classification',
                            '{}'::jsonb
                        )
                        ||
                        jsonb_build_object(
                            'vision_family',
                            COALESCE(
                                dna_json
                                ->'content_classification'
                                ->>'family',
                                ''
                            ),

                            'family',
                            %s,

                            'family_source',
                            'user_explicit_caption',

                            'family_confidence',
                            100
                        )
                    ),

                updated_at = NOW()

            WHERE id = %s

            RETURNING
                user_id,
                brand_id,
                content_family;
            """,
            (
                NEW_FAMILY,
                NEW_FAMILY,
                NEW_FAMILY,
                REFERENCE_ID,
            )
        )

        row = cur.fetchone()

if not row:
    raise RuntimeError(
        "Reference #2 not found"
    )

user_id, brand_id, family = row

print(
    "✅ Reference #2 corrected:",
    family
)

try:
    profile = bm.refresh_brand_visual_profile(
        core,
        user_id,
        brand_id
    )

    print(
        "✅ Brand Visual Profile refreshed"
    )

except Exception as error:
    print(
        "⚠️ Profile refresh:",
        error
    )

print("🚫 No Vision call")
print("🚫 No image generation")
print("🚫 No OpenAI API call")
PY
