"""
Command-line interface for the Paper-Graph system.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.json import JSON

from .agent import PaperGraphAgent
from .config import Config, get_config
from .models import TagType

app = typer.Typer(
    name="paper-graph",
    help="Paper-Graph: Create graph structures from scientific papers using AI tag extraction",
    rich_markup_mode="rich"
)

console = Console()


def print_config_help():
    """Print help for configuration setup."""
    console.print("\n[bold]Configuration Setup[/bold]")
    console.print("Paper-Graph requires a Gemini API key for tag extraction.")
    console.print("You can obtain one from: https://aistudio.google.com/app/apikey")
    console.print("\nSet your API key using one of these methods:")
    console.print("1. Environment variable: export GEMINI_API_KEY='your-key-here'")
    console.print("2. Create a .env file with: GEMINI_API_KEY=your-key-here")
    console.print("3. Pass it directly: --gemini-api-key your-key-here")


@app.command()
def config(
    init: bool = typer.Option(False, "--init", help="Initialize configuration file"),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    file: Optional[str] = typer.Option(None, "--file", help="Configuration file path")
):
    """Manage Paper-Graph configuration."""
    if init:
        config_obj = Config.load_from_env()
        
        if file is None:
            file = ".env"
        
        config_obj.save_to_file(file)
        console.print(f"[green]Configuration template saved to {file}[/green]")
        console.print("Please edit the file and add your API keys.")
        print_config_help()
        
    elif show:
        config_obj = get_config()
        console.print("\n[bold]Current Configuration:[/bold]")
        
        # Show configuration without sensitive data
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Default Sources", ", ".join(config_obj.default_sources))
        table.add_row("Max Results", str(config_obj.max_results_per_search))
        table.add_row("Tag Temperature", str(config_obj.tag_extraction_temperature))
        table.add_row("Max Tags", str(config_obj.max_tags_per_paper))
        table.add_row("API Keys Status", str(config_obj.validate_api_keys()))
        
        console.print(table)
    
    else:
        print_config_help()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for papers"),
    max_results: int = typer.Option(10, "--max-results", "-n", help="Maximum number of results"),
    sources: List[str] = typer.Option(None, "--source", "-s", help="Paper sources (arxiv, pubmed, etc.)"),
    extract_tags: bool = typer.Option(True, "--extract-tags/--no-extract-tags", help="Extract tags after search"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Export results to file"),
    gemini_api_key: Optional[str] = typer.Option(None, "--gemini-api-key", help="Gemini API key")
):
    """Search for papers and add them to the graph."""
    
    async def run_search():
        try:
            # Initialize agent
            agent = PaperGraphAgent(gemini_api_key)
            
            if sources is None:
                sources_list = get_config().default_sources
            else:
                sources_list = sources
            
            console.print(f"[bold]Searching for papers:[/bold] {query}")
            console.print(f"[dim]Sources: {', '.join(sources_list)}[/dim]")
            console.print(f"[dim]Max results: {max_results}[/dim]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Searching papers...", total=None)
                
                result = await agent.process_search_query(
                    query=query,
                    max_results=max_results,
                    sources=sources_list
                )
                
                progress.update(task, description="Search completed!")
            
            # Display results
            console.print(f"\n[green]Found {result['papers_found']} papers[/green]")
            console.print(f"[cyan]Successfully processed: {result['successful_extractions']}/{result['papers_processed']}[/cyan]")
            
            # Show tag statistics
            stats = result['graph_stats']
            console.print(f"\n[bold]Graph Statistics:[/bold]")
            console.print(f"Total papers: {stats['total_papers']}")
            console.print(f"Unique tags: {stats['unique_tags']}")
            console.print(f"Avg tags per paper: {stats['avg_tags_per_paper']:.1f}")
            
            # Export if requested
            if output:
                agent.export_graph(output)
                console.print(f"[green]Results exported to {output}[/green]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if "GEMINI_API_KEY" in str(e):
                print_config_help()
            return 1
        
        return 0
    
    exit_code = asyncio.run(run_search())
    if exit_code != 0:
        sys.exit(exit_code)


@app.command()
def extract(
    paper_id: Optional[str] = typer.Option(None, "--paper-id", help="Extract tags for specific paper"),
    force: bool = typer.Option(False, "--force", help="Force re-extraction of existing tags"),
    import_file: Optional[str] = typer.Option(None, "--import", help="Import graph before extraction"),
    gemini_api_key: Optional[str] = typer.Option(None, "--gemini-api-key", help="Gemini API key")
):
    """Extract tags from papers using Gemini AI."""
    
    async def run_extraction():
        try:
            agent = PaperGraphAgent(gemini_api_key)
            
            # Import graph if specified
            if import_file:
                if not Path(import_file).exists():
                    console.print(f"[red]File {import_file} does not exist[/red]")
                    return 1
                agent.import_graph(import_file)
                console.print(f"[green]Imported graph from {import_file}[/green]")
            
            if paper_id:
                # Extract for specific paper
                console.print(f"[bold]Extracting tags for paper:[/bold] {paper_id}")
                success = await agent.extract_tags_for_paper(paper_id, force)
                
                if success:
                    paper = agent.graph.get_paper(paper_id)
                    console.print(f"[green]Successfully extracted {len(paper.tags)} tags[/green]")
                    
                    # Show extracted tags
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Tag", style="cyan")
                    table.add_column("Type", style="yellow")
                    table.add_column("Confidence", style="green")
                    
                    for tag in paper.tags:
                        table.add_row(tag.name, tag.tag_type.value, f"{tag.confidence:.2f}")
                    
                    console.print(table)
                else:
                    console.print("[red]Failed to extract tags[/red]")
                    return 1
            else:
                # Extract for all papers
                console.print("[bold]Extracting tags for all papers...[/bold]")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Extracting tags...", total=None)
                    
                    results = await agent.extract_tags_for_all_papers(force)
                    
                    progress.update(task, description="Extraction completed!")
                
                successful = sum(results.values())
                total = len(results)
                
                console.print(f"[green]Processed {total} papers[/green]")
                console.print(f"[cyan]Successful: {successful}, Failed: {total - successful}[/cyan]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if "GEMINI_API_KEY" in str(e):
                print_config_help()
            return 1
        
        return 0
    
    exit_code = asyncio.run(run_extraction())
    if exit_code != 0:
        sys.exit(exit_code)


@app.command()
def query(
    tags: List[str] = typer.Option(None, "--tag", help="Filter by tag names"),
    tag_types: List[str] = typer.Option(None, "--type", help="Filter by tag types"),
    sources: List[str] = typer.Option(None, "--source", help="Filter by paper sources"),
    limit: int = typer.Option(20, "--limit", help="Maximum number of results"),
    import_file: Optional[str] = typer.Option(None, "--import", help="Import graph before querying"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Export results to file"),
    format: str = typer.Option("table", "--format", help="Output format (table, json)")
):
    """Query papers in the graph."""
    
    async def run_query():
        try:
            agent = PaperGraphAgent()
            
            # Import graph if specified
            if import_file:
                if not Path(import_file).exists():
                    console.print(f"[red]File {import_file} does not exist[/red]")
                    return 1
                agent.import_graph(import_file)
            
            # Validate tag types
            valid_tag_types = []
            if tag_types:
                for tag_type in tag_types:
                    try:
                        valid_tag_types.append(TagType(tag_type.lower()))
                    except ValueError:
                        console.print(f"[yellow]Warning: Invalid tag type '{tag_type}', skipping[/yellow]")
            
            # Create query request
            from .models import GraphQueryRequest
            query_request = GraphQueryRequest(
                tag_filter=tags,
                tag_type_filter=valid_tag_types if valid_tag_types else None,
                source_filter=sources
            )
            
            # Execute query
            papers = agent.graph.query_papers(query_request)
            papers = papers[:limit]  # Apply limit
            
            if not papers:
                console.print("[yellow]No papers found matching the criteria[/yellow]")
                return 0
            
            console.print(f"[green]Found {len(papers)} papers[/green]")
            
            if format == "json":
                # JSON output
                result = [paper.to_dict() for paper in papers]
                console.print(JSON.from_data(result))
            else:
                # Table output
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Title", style="cyan", max_width=50)
                table.add_column("Authors", style="yellow", max_width=30)
                table.add_column("Source", style="green")
                table.add_column("Tags", style="blue", max_width=40)
                
                for paper in papers:
                    authors = ", ".join(paper.authors[:2])
                    if len(paper.authors) > 2:
                        authors += f" (+{len(paper.authors)-2})"
                    
                    tag_names = [tag.name for tag in paper.tags[:3]]
                    if len(paper.tags) > 3:
                        tag_names.append(f"(+{len(paper.tags)-3})")
                    
                    table.add_row(
                        paper.title[:47] + "..." if len(paper.title) > 50 else paper.title,
                        authors,
                        paper.source,
                        ", ".join(tag_names)
                    )
                
                console.print(table)
            
            # Export if requested
            if output:
                result_data = [paper.to_dict() for paper in papers]
                with open(output, 'w') as f:
                    import json
                    json.dump(result_data, f, indent=2, default=str)
                console.print(f"[green]Results exported to {output}[/green]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1
        
        return 0
    
    exit_code = asyncio.run(run_query())
    if exit_code != 0:
        sys.exit(exit_code)


@app.command()
def stats(
    import_file: Optional[str] = typer.Option(None, "--import", help="Import graph before showing stats")
):
    """Show graph statistics."""
    
    async def run_stats():
        try:
            agent = PaperGraphAgent()
            
            # Import graph if specified
            if import_file:
                if not Path(import_file).exists():
                    console.print(f"[red]File {import_file} does not exist[/red]")
                    return 1
                agent.import_graph(import_file)
                console.print(f"[dim]Loaded graph from {import_file}[/dim]\n")
            
            # Get statistics
            summary = agent.get_graph_summary()
            
            # Display statistics
            console.print("[bold]Paper-Graph Statistics[/bold]\n")
            
            # Basic stats
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            stats = summary["tag_statistics"]
            table.add_row("Total Papers", str(stats["total_papers"]))
            table.add_row("Total Tags", str(stats["total_tags"]))
            table.add_row("Unique Tags", str(stats["unique_tags"]))
            table.add_row("Avg Tags/Paper", f"{stats['avg_tags_per_paper']:.1f}")
            
            console.print(table)
            
            # Processing status
            console.print("\n[bold]Processing Status:[/bold]")
            status_table = Table(show_header=True, header_style="bold magenta")
            status_table.add_column("Status", style="cyan")
            status_table.add_column("Count", style="green")
            
            for status, count in summary["processing_status"].items():
                status_table.add_row(status.title(), str(count))
            
            console.print(status_table)
            
            # Most common tags
            if stats["most_common_tags"]:
                console.print("\n[bold]Most Common Tags:[/bold]")
                tag_table = Table(show_header=True, header_style="bold magenta")
                tag_table.add_column("Tag", style="cyan")
                tag_table.add_column("Papers", style="green")
                
                for tag, count in stats["most_common_tags"]:
                    tag_table.add_row(tag, str(count))
                
                console.print(tag_table)
            
            # Graph metrics
            if summary["graph_metrics"]:
                console.print("\n[bold]Graph Metrics:[/bold]")
                metrics_table = Table(show_header=True, header_style="bold magenta")
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Value", style="green")
                
                metrics = summary["graph_metrics"]
                for key, value in metrics.items():
                    if value is not None:
                        if isinstance(value, float):
                            value = f"{value:.3f}"
                        metrics_table.add_row(key.replace("_", " ").title(), str(value))
                
                console.print(metrics_table)
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1
        
        return 0
    
    exit_code = asyncio.run(run_stats())
    if exit_code != 0:
        sys.exit(exit_code)


@app.command()
def server(
    host: str = typer.Option("localhost", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    gemini_api_key: Optional[str] = typer.Option(None, "--gemini-api-key", help="Gemini API key")
):
    """Start the MCP server."""
    console.print(f"[bold]Starting Paper-Graph MCP Server[/bold]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")
    
    try:
        from .server import mcp
        import uvicorn
        uvicorn.run(mcp, host=host, port=port)
    except ImportError:
        console.print("[red]uvicorn is required to run the server. Install with: pip install uvicorn[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()