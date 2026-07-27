# Orders micro-frontend

This Module Federation remote renders order screens inside the authenticated customer portal. It has no server, BFF, serverless function, database, gateway policy, session implementation, or trusted authorization policy. The host supplies display claims and an access token.

The `/api/orders` implementation and its object, tenant, and function authorization are owned by the separate `orders-api` repository. Client role checks are navigation hints only.
