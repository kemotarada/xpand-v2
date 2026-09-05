def _self_test_final_locks():
    txt = build_final_render_locks_text(
        user_text="خدمات التجارة الإلكترونية ونقاط البيع",
        explicit_benefit_family="merchant_payments",
        selected_stc_style="premium_realistic",
    )

    assert "Do not create a giant blank upper area." in txt or "Do not leave a giant empty upper third" in txt
    assert "Do not invent payment hardware." in txt
    assert "Do not create a physically impossible phone-and-POS fusion object." in txt
    print("✅ final_render_locks_regression")
