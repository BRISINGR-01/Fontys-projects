from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from data import EvolutionAnalyzer
from math import ceil
import requests
import json
from pathlib import Path
from typing import Dict, Optional, Any
import os
from urllib.parse import urlparse

app = Flask(__name__)
analyzer = EvolutionAnalyzer('pokemon.csv')
POKEMON_LIST = sorted(analyzer.df['name'].unique())
ITEMS_PER_PAGE = 50

# Configure cache directories
CACHE_DIR = Path('static/pokemon_cache')
SPRITES_DIR = CACHE_DIR / 'sprites'
ARTWORK_DIR = CACHE_DIR / 'artwork'
CACHE_INDEX = CACHE_DIR / 'sprite_index.json'

# Create cache directories if they don't exist
SPRITES_DIR.mkdir(parents=True, exist_ok=True)
ARTWORK_DIR.mkdir(parents=True, exist_ok=True)

def load_cache_index() -> Dict[str, Any]:
    """Load the cache index from disk."""
    if CACHE_INDEX.exists():
        with open(CACHE_INDEX, 'r') as f:
            return json.load(f)
    return {}

def save_cache_index(index: Dict[str, Any]) -> None:
    """Save the cache index to disk."""
    with open(CACHE_INDEX, 'w') as f:
        json.dump(index, f)

def download_image(url: str, cache_dir: Path) -> Path:
    """Download an image and save it locally."""
    if not url:
        return None
        
    # Extract filename from URL
    filename = os.path.basename(urlparse(url).path)
    local_path = cache_dir / filename
    
    # Download if not already cached
    if not local_path.exists():
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return local_path
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None
            
    return local_path

def get_evolution_sprites(evolution_chain: list) -> Dict[str, Any]:
    """Get sprites for all Pokemon in the evolution chain with error caching."""
    cache_index = load_cache_index()
    sprites = {}
    
    for pokemon in evolution_chain:
        pokemon_lower = pokemon.lower()
        
        # Check if Pokemon is in cache (including error states)
        if pokemon_lower in cache_index:
            sprites[pokemon] = cache_index[pokemon_lower]
            continue
            
        try:
            response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_lower}')
            response.raise_for_status()
            data = response.json()
            
            sprite_data = {
                'types': [t['type']['name'] for t in data['types']],
                'sprites': {},
                'error': None  # No error
            }
            
            # Process regular sprites
            for view in ['front_default', 'back_default']:
                url = data['sprites'][view]
                if url:
                    try:
                        local_path = download_image(url, SPRITES_DIR)
                        if local_path:
                            sprite_data['sprites'][view] = f'/static/pokemon_cache/sprites/{local_path.name}'
                    except Exception as e:
                        print(f"Error downloading {view} sprite for {pokemon}: {e}")
            
            # Process official artwork
            artwork_url = data['sprites']['other']['official-artwork']['front_default']
            if artwork_url:
                try:
                    local_path = download_image(artwork_url, ARTWORK_DIR)
                    if local_path:
                        sprite_data['sprites']['official'] = f'/static/pokemon_cache/artwork/{local_path.name}'
                except Exception as e:
                    print(f"Error downloading artwork for {pokemon}: {e}")
            
        except Exception as e:
            print(f"Error fetching data for {pokemon}: {e}")
            # Cache the error state
            sprite_data = {
                'error': str(e),
                'types': [],
                'sprites': {}
            }
        
        cache_index[pokemon_lower] = sprite_data
        sprites[pokemon] = sprite_data
    
    # Save updated cache index
    save_cache_index(cache_index)
    return sprites

def get_pokemon_sprite(pokemon_name: str) -> Optional[Dict[str, Any]]:
    """Get sprite data for a single Pokemon with error caching."""
    cache_index = load_cache_index()
    pokemon_lower = pokemon_name.lower()
    
    # Check if Pokemon is in cache (including error states)
    if pokemon_lower in cache_index:
        return cache_index[pokemon_lower]
    
    try:
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_lower}')
        response.raise_for_status()
        data = response.json()
        
        sprite_data = {
            'types': [t['type']['name'] for t in data['types']],
            'sprites': {},
            'error': None  # No error
        }
        
        # Cache front sprite
        front_url = data['sprites']['front_default']
        if front_url:
            try:
                local_path = download_image(front_url, SPRITES_DIR)
                if local_path:
                    sprite_data['sprites']['front_default'] = f'/static/pokemon_cache/sprites/{local_path.name}'
            except Exception as e:
                print(f"Error downloading sprite for {pokemon_name}: {e}")
                # Don't fail completely if just the sprite download fails
        
    except Exception as e:
        print(f"Error fetching data for {pokemon_name}: {e}")
        # Cache the error state
        sprite_data = {
            'error': str(e),
            'types': [],
            'sprites': {}
        }
    
    # Cache the result (success or failure)
    cache_index[pokemon_lower] = sprite_data
    save_cache_index(cache_index)
    return sprite_data

@app.route('/')
def index():
    pokemon_data = []
    for pokemon in POKEMON_LIST:
        sprite_data = get_pokemon_sprite(pokemon)
        pokemon_data.append({
            'name': pokemon,
            'sprite_data': sprite_data
        })
    
    return render_template('index.html', pokemon_list=pokemon_data)

@app.route('/api/search')
def search_pokemon():
    query = request.args.get('q', '').lower()
    results = [
        {'name': pokemon} 
        for pokemon in POKEMON_LIST 
        if query in pokemon.lower()
    ][:10]
    return jsonify(results)

@app.route('/api/pokemon/<name>')
def get_pokemon_data(name):
    changes, stats_df, _ = analyzer.calculate_evolution_value(name)
    return jsonify({
        'changes': changes,
        'stats': stats_df.to_dict() if not stats_df.empty else None
    })

@app.route('/pokemon/<name>')
def pokemon_details(name):
    if name not in POKEMON_LIST:
        return redirect(url_for('index'))
        
    changes, stats_df, _ = analyzer.calculate_evolution_value(name)
    evolution_chain = list(stats_df.index) if not stats_df.empty else [name]
    sprites = get_evolution_sprites(evolution_chain)
    
    return render_template('pokemon.html', 
                         pokemon_name=name,
                         changes=changes,
                         stats_df=stats_df if not stats_df.empty else None,
                         sprites=sprites)

if __name__ == '__main__':
    app.run(debug=True) 