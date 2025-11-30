"""Module defines the main entry point for the Apify Actor.

This Actor searches for 3D models on Sketchfab using the provided input parameters.
"""

from __future__ import annotations

from apify import Actor
from httpx import AsyncClient


async def main() -> None:
    """Define a main entry point for the Apify Actor."""
    async with Actor:
        # Retrieve the input object for the Actor.
        actor_input = await Actor.get_input() or {}

        # Construct query parameters, filtering out None and empty values
        params = {'type': 'models'}
        for key, value in actor_input.items():
            if value is not None and value != "" and value != []:
                params[key] = value

        # Make the request to Sketchfab API
        url = 'https://api.sketchfab.com/v3/search'
        async with AsyncClient() as client:
            Actor.log.info(f'Sending request to {url} with params: {params}')
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Push each result to the dataset
        results = data.get('results', [])
        for result in results:
            await Actor.push_data(result)

        Actor.log.info(f'Pushed {len(results)} results to dataset')
