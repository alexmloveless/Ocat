"""
Vector store operation commands for Ocat.

Implements commands for managing the conversation vector store.
"""

from typing import List, Any
from rich.table import Table
from rich.panel import Panel

from . import command, BaseCommand, CommandResult
from ..productivity.models import EntityType


@command(
    name="vadd",
    description="Add a text document to the vector store",
    usage="/vadd <text>",
)
class VectorAddCommand(BaseCommand):
    """Command to add text to the vector store."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the vadd command.

        Parameters
        ----------
        args : List[str]
            Command arguments - text to add
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error("No text specified. Usage: /vadd <text>")

        try:
            # Check if vector store is enabled
            if not context.config.vector_store.enabled:
                return CommandResult.error(
                    "Vector store is not enabled in configuration."
                )

            if not hasattr(context, "vector_store") or context.vector_store is None:
                return CommandResult.error("Vector store is not initialized.")

            # Join all arguments as the text to add
            text_content = " ".join(args)

            # Add to vector store using the correct method
            exchange_id = context.vector_store.add_exchange(
                user_prompt=text_content,
                assistant_response="[Manual addition to vector store]",
                thread_id=getattr(context, "thread_id", "manual"),
                session_id=getattr(context, "session_id", "manual"),
            )

            context.console.print(
                f"✅ Text added to vector store with ID: {exchange_id}", style="green"
            )

            return CommandResult.ok(
                f"Added text to vector store with ID: {exchange_id}"
            )

        except Exception as e:
            return CommandResult.error(f"Failed to add to vector store: {e}")


@command(
    name="vdelete",
    description="Delete a document by ID",
    usage="/vdelete <id>",
)
class VectorDeleteCommand(BaseCommand):
    """Command to delete an exchange from the vector store by ID."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the vdelete command.

        Parameters
        ----------
        args : List[str]
            Command arguments - exchange ID to delete
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error("No ID specified. Usage: /vdelete <id>")

        try:
            # Check if vector store is enabled
            if not context.config.vector_store.enabled:
                return CommandResult.error(
                    "Vector store is not enabled in configuration."
                )

            if not hasattr(context, "vector_store") or context.vector_store is None:
                return CommandResult.error("Vector store is not initialized.")

            exchange_id = args[0]

            # Try to delete from vector store
            success = context.vector_store.delete_exchange(exchange_id)

            if success:
                context.console.print(
                    f"✅ Deleted exchange with ID: {exchange_id}", style="green"
                )
                return CommandResult.ok(f"Deleted exchange: {exchange_id}")
            else:
                return CommandResult.error(
                    f"Exchange with ID '{exchange_id}' not found."
                )

        except Exception as e:
            return CommandResult.error(f"Failed to delete from vector store: {e}")


@command(
    name="vget",
    description="Retrieve a specific exchange by ID, or all exchanges by session/thread ID",
    usage="/vget <id> | /vget session <session_id> | /vget thread <thread_id>",
)
class VectorGetCommand(BaseCommand):
    """Command to retrieve and display a specific exchange by ID, or all exchanges by session/thread ID."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the vget command.

        Parameters
        ----------
        args : List[str]
            Command arguments - exchange ID to retrieve, or session/thread type and ID
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No ID specified. Usage: /vget <id> | /vget session <session_id> | /vget thread <thread_id>"
            )

        try:
            # Check if vector store is enabled
            if not context.config.vector_store.enabled:
                return CommandResult.error(
                    "Vector store is not enabled in configuration."
                )

            if not hasattr(context, "vector_store") or context.vector_store is None:
                return CommandResult.error("Vector store is not initialized.")

            # Check if this is a session or thread query
            if len(args) >= 2 and args[0].lower() in ["session", "thread"]:
                query_type = args[0].lower()
                query_id = args[1]

                if query_type == "session":
                    exchanges = context.vector_store.get_exchanges_by_session_id(
                        query_id
                    )
                    title = f"Session: {query_id}"
                else:  # thread
                    exchanges = context.vector_store.get_exchanges_by_thread_id(
                        query_id
                    )
                    title = f"Thread: {query_id}"

                if not exchanges:
                    return CommandResult.error(
                        f"No exchanges found for {query_type} ID '{query_id}'."
                    )

                # Display all exchanges for the session/thread
                for i, exchange in enumerate(exchanges):
                    exchange_panel = Panel(
                        f"**Exchange ID:** {exchange.exchange_id}\n"
                        f"**Thread ID:** {exchange.thread_id}\n"
                        f"**Session ID:** {exchange.session_id}\n\n"
                        f"**User:** {exchange.user_prompt}\n\n"
                        f"**Assistant:** {exchange.assistant_response}",
                        title=f"{title} - Exchange {i+1}/{len(exchanges)}",
                        border_style="blue",
                    )
                    context.console.print(exchange_panel)
                    context.console.print()  # Add spacing between exchanges

                return CommandResult.ok(
                    f"Retrieved {len(exchanges)} exchanges for {query_type}: {query_id}"
                )

            else:
                # Original behavior - get single exchange by ID
                exchange_id = args[0]
                exchange = context.vector_store.get_exchange_by_id(exchange_id)

                if exchange:
                    # Display the exchange
                    exchange_panel = Panel(
                        f"**Exchange ID:** {exchange.exchange_id}\n"
                        f"**Thread ID:** {exchange.thread_id}\n"
                        f"**Session ID:** {exchange.session_id}\n\n"
                        f"**User:** {exchange.user_prompt}\n\n"
                        f"**Assistant:** {exchange.assistant_response}",
                        title=f"Exchange: {exchange_id}",
                        border_style="blue",
                    )
                    context.console.print(exchange_panel)

                    return CommandResult.ok(f"Retrieved exchange: {exchange_id}")
                else:
                    return CommandResult.error(
                        f"Exchange with ID '{exchange_id}' not found."
                    )

        except Exception as e:
            return CommandResult.error(f"Failed to retrieve from vector store: {e}")


@command(
    name="vquery",
    description="Query similar exchanges from vector store",
    usage="/vquery <query> [k]",
)
class VectorQueryCommand(BaseCommand):
    """Command to search for similar exchanges in the vector store."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the vquery command.

        Parameters
        ----------
        args : List[str]
            Command arguments - query text and optional number of results
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error("No query specified. Usage: /vquery <query> [k]")

        try:
            # Check if vector store is enabled
            if not context.config.vector_store.enabled:
                return CommandResult.error(
                    "Vector store is not enabled in configuration."
                )

            if not hasattr(context, "vector_store") or context.vector_store is None:
                return CommandResult.error("Vector store is not initialized.")

            # Parse arguments
            query_text = (
                " ".join(args[:-1])
                if len(args) > 1 and args[-1].isdigit()
                else " ".join(args)
            )
            k = int(args[-1]) if len(args) > 1 and args[-1].isdigit() else 5

            # Query vector store
            similar_exchanges = context.vector_store.find_similar_exchanges(
                query_text=query_text, n_results=k
            )

            if not similar_exchanges:
                return CommandResult.ok("No similar exchanges found.")

            # Display results
            results_table = Table(
                title=f"Similar Exchanges (Top {len(similar_exchanges)})"
            )
            results_table.add_column("ID", style="cyan", no_wrap=True)
            results_table.add_column("User Prompt", style="white")
            results_table.add_column("Assistant Response", style="green")

            for exchange in similar_exchanges:
                # Truncate long content
                user_truncated = (
                    (exchange.user_prompt[:60] + "...")
                    if len(exchange.user_prompt) > 60
                    else exchange.user_prompt
                )
                assistant_truncated = (
                    (exchange.assistant_response[:60] + "...")
                    if len(exchange.assistant_response) > 60
                    else exchange.assistant_response
                )

                results_table.add_row(
                    exchange.exchange_id, user_truncated, assistant_truncated
                )

            context.console.print(results_table)
            context.console.print()

            return CommandResult.ok(
                f"Found {len(similar_exchanges)} similar exchanges."
            )

        except Exception as e:
            return CommandResult.error(f"Failed to query vector store: {e}")


@command(
    name="vstats",
    description="Display vector store statistics",
    usage="/vstats",
)
class VectorStatsCommand(BaseCommand):
    """Command to display vector store statistics and information."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the vstats command.

        Parameters
        ----------
        args : List[str]
            Command arguments (unused)
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Check if vector store is enabled
            if not context.config.vector_store.enabled:
                return CommandResult.error(
                    "Vector store is not enabled in configuration."
                )

            if not hasattr(context, "vector_store") or context.vector_store is None:
                return CommandResult.error("Vector store is not initialized.")

            # Get statistics from vector store
            stats = context.vector_store.get_stats()

            # Create statistics display
            stats_table = Table(title="Vector Store Statistics")
            stats_table.add_column("Metric", style="cyan", no_wrap=True)
            stats_table.add_column("Value", style="white")

            # Display basic statistics
            stats_table.add_row("Total Exchanges", str(stats.get("total_exchanges", 0)))
            stats_table.add_row(
                "Conversation Exchanges", str(stats.get("conversation_exchanges", 0))
            )
            stats_table.add_row(
                "Productivity Exchanges", str(stats.get("productivity_exchanges", 0))
            )
            stats_table.add_row("Total Vectors", str(stats.get("index_size", 0)))
            stats_table.add_row("Embedding Model", context.config.embedding.model)
            stats_table.add_row(
                "Embedding Dimensions", str(context.config.embedding.dimensions)
            )
            stats_table.add_row("Vector Store Path", context.config.vector_store.path)
            stats_table.add_row(
                "Similarity Threshold",
                str(context.config.vector_store.similarity_threshold),
            )
            stats_table.add_row(
                "Chat Window", str(context.config.vector_store.chat_window)
            )
            stats_table.add_row(
                "Context Results", str(context.config.vector_store.context_results)
            )

            # Add memory statistics if available
            if "memory_stats" in stats:
                memory_stats = stats["memory_stats"]
                stats_table.add_row(
                    "Memory Checkpoints", str(memory_stats.get("checkpoints", 0))
                )
                stats_table.add_row(
                    "Active Threads", str(memory_stats.get("active_threads", 0))
                )

            context.console.print(stats_table)
            context.console.print()

            # Display productivity object counts
            if (
                hasattr(context, "productivity_storage")
                and context.productivity_storage
            ):
                prod_table = Table(title="Productivity Objects")
                prod_table.add_column("Object Type", style="cyan", no_wrap=True)
                prod_table.add_column("Count", style="white")

                # Count each entity type
                for entity_type in EntityType:
                    entities = context.productivity_storage.get_entities_by_type(
                        entity_type, limit=1000
                    )
                    count = len(entities)
                    prod_table.add_row(entity_type.value.title(), str(count))

                # Add total productivity objects
                all_entities = []
                for entity_type in EntityType:
                    all_entities.extend(
                        context.productivity_storage.get_entities_by_type(
                            entity_type, limit=1000
                        )
                    )
                prod_table.add_row("Total Productivity", str(len(all_entities)))

                context.console.print(prod_table)
                context.console.print()

            # Display recent activity if available
            if "recent_activity" in stats:
                recent_table = Table(title="Recent Activity")
                recent_table.add_column("Exchange ID", style="cyan")
                recent_table.add_column("Thread ID", style="yellow")
                recent_table.add_column("User Prompt", style="white")

                for activity in stats["recent_activity"][:5]:  # Show last 5
                    user_prompt = activity.get("user_prompt", "")
                    truncated = (
                        (user_prompt[:50] + "...")
                        if len(user_prompt) > 50
                        else user_prompt
                    )
                    recent_table.add_row(
                        activity.get("exchange_id", ""),
                        activity.get("thread_id", ""),
                        truncated,
                    )

                context.console.print(recent_table)

            return CommandResult.ok("Vector store statistics displayed.")

        except Exception as e:
            return CommandResult.error(f"Failed to get vector store statistics: {e}")
