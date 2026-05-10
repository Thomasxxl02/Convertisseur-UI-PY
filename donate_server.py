#!/usr/bin/env python3
"""Serveur local pour la page de don et creation d'une session Stripe Checkout."""

from __future__ import annotations

import os
from pathlib import Path

import stripe
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PORT = 8787
MIN_AMOUNT_EUR = 1
MAX_AMOUNT_EUR = 10000
DEFAULT_STRIPE_PRODUCT_ID = "prod_UUeI06vtxJmMsz"
DEFAULT_STRIPE_TAX_CODE = "txcd_10000000"


app = Flask(__name__)


@app.get("/")
def donation_page():
    return send_from_directory(BASE_DIR, "page_don.html")


@app.get("/health")
def health_check():
    return jsonify({"ok": True})


@app.post("/api/create-checkout-session")
def create_checkout_session():
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe_secret_key:
        return (
            jsonify({"error": "STRIPE_SECRET_KEY manquante. Configure ta variable d'environnement."}),
            500,
        )

    stripe.api_key = stripe_secret_key
    stripe_product_id = os.getenv("STRIPE_PRODUCT_ID", DEFAULT_STRIPE_PRODUCT_ID).strip()
    stripe_tax_code = os.getenv("STRIPE_PRODUCT_TAX_CODE", DEFAULT_STRIPE_TAX_CODE).strip()

    payload = request.get_json(silent=True) or {}
    amount_raw = payload.get("amount")
    full_name = str(payload.get("fullName") or "").strip()
    email = str(payload.get("email") or "").strip()
    message = str(payload.get("message") or "").strip()

    try:
        amount_eur = int(amount_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "Montant invalide."}), 400

    if amount_eur < MIN_AMOUNT_EUR or amount_eur > MAX_AMOUNT_EUR:
        return (
            jsonify(
                {
                    "error": (
                        f"Le montant doit etre compris entre {MIN_AMOUNT_EUR} et {MAX_AMOUNT_EUR} EUR."
                    )
                }
            ),
            400,
        )

    if not full_name:
        return jsonify({"error": "Nom obligatoire."}), 400
    if not email:
        return jsonify({"error": "Email obligatoire."}), 400

    success_url = os.getenv(
        "STRIPE_SUCCESS_URL",
        f"http://localhost:{DEFAULT_PORT}/?payment=success",
    )
    cancel_url = os.getenv(
        "STRIPE_CANCEL_URL",
        f"http://localhost:{DEFAULT_PORT}/?payment=cancel",
    )

    metadata = {
        "full_name": full_name,
    }
    if message:
        metadata["message"] = message[:500]

    try:
        # Aligne le tax code du produit si un tax code est fourni.
        if stripe_product_id and stripe_tax_code:
            stripe.Product.modify(
                stripe_product_id,
                tax_code=stripe_tax_code,
            )

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            customer_email=email,
            metadata=metadata,
            automatic_tax={"enabled": True},
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": amount_eur * 100,
                        "product": stripe_product_id,
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as exc:
        return jsonify({"error": f"Erreur Stripe: {exc.user_message or str(exc)}"}), 502
    except Exception:
        return jsonify({"error": "Erreur interne lors de la creation de session Stripe."}), 500

    return jsonify({"checkoutUrl": session.url})


if __name__ == "__main__":
    port = int(os.getenv("DONATION_PORT", str(DEFAULT_PORT)))
    app.run(host="127.0.0.1", port=port, debug=False)
