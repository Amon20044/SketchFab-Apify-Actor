## Sketchfab Model Search Actor

<!-- This is an Apify Actor for searching 3D models on Sketchfab -->

A Python-based Apify Actor that searches for 3D models on [Sketchfab](https://sketchfab.com) using their public API. It accepts various input filters to narrow down the search and outputs detailed model metadata to a dataset.

The Actor queries the Sketchfab API endpoint `https://api.sketchfab.com/v3/search?type=models` with user-defined parameters and stores each matching model as a structured JSON object in the dataset.

## Included features

- **[Apify SDK](https://docs.apify.com/sdk/python/)** for Python - a toolkit for building Apify Actors
- **[Input schema](https://docs.apify.com/platform/actors/development/input-schema)** - comprehensive input validation for search filters
- **[Dataset](https://docs.apify.com/sdk/python/docs/concepts/storages#working-with-datasets)** - stores model results with fields like UID, name, user, thumbnails, archives, etc.
- **[HTTPX](https://www.python-httpx.org)** - asynchronous HTTP client for API requests

## Supported Filters

The Actor supports a wide range of Sketchfab search filters:

- **Keywords** (`q`): Space-separated search terms
- **User** (`user`): Search by uploader username
- **Tags & Categories**: Arrays of tag/category slugs
- **Date Range** (`date`): Limit to models uploaded in last X days
- **Downloadability** (`downloadable`): Filter by download permissions
- **Animation & Sound**: Include animated or sound-enabled models
- **Staff Picks** (`staffpicked`): Show only staff-curated models
- **Polygon Count**: Min/max face count filters
- **PBR Types**: Metalness, Specular, or any PBR models
- **Rigging** (`rigged`): Only rigged models
- **Collections**: Search within specific Sketchfab collections
- **Sorting**: By likes, views, date, etc.
- **File Formats**: Filter by available formats (GLTF, OBJ, FBX, etc.)
- **Licenses**: CC-BY, CC0, etc.
- **Archive Filters**: Size, face/vertex counts, texture resolution limits

## How it works

1. `Actor.get_input()` retrieves the search filters from the input schema
2. Constructs query parameters, filtering out empty/null values
3. `httpx.AsyncClient().get()` makes the API request to Sketchfab
4. Parses the JSON response containing model results
5. `Actor.push_data()` stores each model object in the dataset

## Output Data Structure

Each dataset item includes:
- `uid`: Unique model identifier
- `name`: Model title
- `user`: Uploader information (username, profile, avatar)
- `viewerUrl`: Link to view the model
- `publishedAt`: Upload date
- `likeCount`, `viewCount`, `commentCount`: Engagement metrics
- `isDownloadable`: Download availability
- `thumbnails`: Image previews in multiple sizes
- `archives`: Downloadable file information (GLB, GLTF, USDZ, etc.)
- `license`: Creative Commons license type
- And more metadata fields

## Resources

- [Sketchfab API Documentation](https://docs.sketchfab.com/data-api/v3/index.html)
- [Apify Python SDK Docs](https://docs.apify.com/sdk/python)
- [HTTPX Documentation](https://www.python-httpx.org)
- [Apify Platform Documentation](https://docs.apify.com/platform)
- [Join our developer community on Discord](https://discord.com/invite/jyEM2PRvMU)

## Getting started

For complete information [see this article](https://docs.apify.com/platform/actors/development#build-actor-locally). To run the Actor locally use:

```bash
apify run
```

## Deploy to Apify

### Connect Git repository to Apify

If you've created a Git repository for the project, you can easily connect to Apify:

1. Go to [Actor creation page](https://console.apify.com/actors/new)
2. Click on **Link Git Repository** button

### Push project on your local machine to Apify

You can also deploy the project on your local machine to Apify without the need for the Git repository.

1. Log in to Apify. You will need to provide your [Apify API Token](https://console.apify.com/account/integrations) to complete this action.

    ```bash
    apify login
    ```

2. Deploy your Actor. This command will deploy and build the Actor on the Apify Platform. You can find your newly created Actor under [Actors -> My Actors](https://console.apify.com/actors?tab=my).

    ```bash
    apify push
    ```

## Documentation reference

To learn more about Apify and Actors, take a look at the following resources:

- [Apify SDK for Python documentation](https://docs.apify.com/sdk/python)
- [Apify Platform documentation](https://docs.apify.com/platform)
- [Sketchfab Data API](https://docs.sketchfab.com/data-api/v3/index.html)
- [Join our developer community on Discord](https://discord.com/invite/jyEM2PRvMU)
