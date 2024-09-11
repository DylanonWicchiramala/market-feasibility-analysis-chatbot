## code reference: https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/#setup-model-and-tools-for-the-graph

import os
import utils
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple

from langchain_core.runnables import RunnableConfig
from pymongo import MongoClient, UpdateOne
from pymongo.database import Database as MongoDatabase

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
)

utils.load_env()

mongo = os.environ.get('MONGODB_PASS')
uri = f"mongodb+srv://dylan:{mongo}@cluster0.wl8mbpy.mongodb.net/"


# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# db = client["FeasibilityAnalysis"]
# history = db["Chat History"]



class MongoDBSaver(BaseCheckpointSaver):
    """A checkpoint saver that stores checkpoints in a MongoDB database."""

    client: MongoClient
    db: MongoDatabase

    def __init__(
        self,
        client: MongoClient=client,
        db_name: str="FeasibilityAnalysis",
    ) -> None:
        super().__init__()
        self.client = client
        self.db = self.client[db_name]

    @classmethod
    @contextmanager
    def from_conn_info(
        cls, *, host: str, port: int, db_name: str
    ) -> Iterator["MongoDBSaver"]:
        client = None
        try:
            client = MongoClient(host=host, port=port)
            yield MongoDBSaver(client, db_name)
        finally:
            if client:
                client.close()
                
    def close(self):
        self.client.close()

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple from the database.

        This method retrieves a checkpoint tuple from the MongoDB database based on the
        provided config. If the config contains a "checkpoint_id" key, the checkpoint with
        the matching thread ID and checkpoint ID is retrieved. Otherwise, the latest checkpoint
        for the given thread ID is retrieved.

        Args:
            config (RunnableConfig): The config to use for retrieving the checkpoint.

        Returns:
            Optional[CheckpointTuple]: The retrieved checkpoint tuple, or None if no matching checkpoint was found.
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        if checkpoint_id := get_checkpoint_id(config):
            query = {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        else:
            query = {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns}

        result = self.db["checkpoints"].find(query).sort("checkpoint_id", -1).limit(1)
        for doc in result:
            config_values = {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": doc["checkpoint_id"],
            }
            checkpoint = self.serde.loads_typed((doc["type"], doc["checkpoint"]))
            serialized_writes = self.db["checkpoint_writes"].find(config_values)
            pending_writes = [
                (
                    doc["task_id"],
                    doc["channel"],
                    self.serde.loads_typed((doc["type"], doc["value"])),
                )
                for doc in serialized_writes
            ]
            return CheckpointTuple(
                {"configurable": config_values},
                checkpoint,
                self.serde.loads(doc["metadata"]),
                (
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": doc["parent_checkpoint_id"],
                        }
                    }
                    if doc.get("parent_checkpoint_id")
                    else None
                ),
                pending_writes,
            )

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints from the database.

        This method retrieves a list of checkpoint tuples from the MongoDB database based
        on the provided config. The checkpoints are ordered by checkpoint ID in descending order (newest first).

        Args:
            config (RunnableConfig): The config to use for listing the checkpoints.
            filter (Optional[Dict[str, Any]]): Additional filtering criteria for metadata. Defaults to None.
            before (Optional[RunnableConfig]): If provided, only checkpoints before the specified checkpoint ID are returned. Defaults to None.
            limit (Optional[int]): The maximum number of checkpoints to return. Defaults to None.

        Yields:
            Iterator[CheckpointTuple]: An iterator of checkpoint tuples.
        """
        query = {}
        if config is not None:
            query = {
                "thread_id": config["configurable"]["thread_id"],
                "checkpoint_ns": config["configurable"].get("checkpoint_ns", ""),
            }

        if filter:
            for key, value in filter.items():
                query[f"metadata.{key}"] = value

        if before is not None:
            query["checkpoint_id"] = {"$lt": before["configurable"]["checkpoint_id"]}

        result = self.db["checkpoints"].find(query).sort("checkpoint_id", -1)

        if limit is not None:
            result = result.limit(limit)
        for doc in result:
            checkpoint = self.serde.loads_typed((doc["type"], doc["checkpoint"]))
            yield CheckpointTuple(
                {
                    "configurable": {
                        "thread_id": doc["thread_id"],
                        "checkpoint_ns": doc["checkpoint_ns"],
                        "checkpoint_id": doc["checkpoint_id"],
                    }
                },
                checkpoint,
                self.serde.loads(doc["metadata"]),
                (
                    {
                        "configurable": {
                            "thread_id": doc["thread_id"],
                            "checkpoint_ns": doc["checkpoint_ns"],
                            "checkpoint_id": doc["parent_checkpoint_id"],
                        }
                    }
                    if doc.get("parent_checkpoint_id")
                    else None
                ),
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to the database.

        This method saves a checkpoint to the MongoDB database. The checkpoint is associated
        with the provided config and its parent config (if any).

        Args:
            config (RunnableConfig): The config to associate with the checkpoint.
            checkpoint (Checkpoint): The checkpoint to save.
            metadata (CheckpointMetadata): Additional metadata to save with the checkpoint.
            new_versions (ChannelVersions): New channel versions as of this write.

        Returns:
            RunnableConfig: Updated configuration after storing the checkpoint.
        """
        timestamp = datetime.now()
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = checkpoint["id"]
        type_, serialized_checkpoint = self.serde.dumps_typed(checkpoint)
        doc = {
            "parent_checkpoint_id": config["configurable"].get("checkpoint_id"),
            "type": type_,
            "checkpoint": serialized_checkpoint,
            "metadata": self.serde.dumps(metadata),
            "timestamp": timestamp,
        }
        upsert_query = {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint_id,
        }
        # Perform your operations here
        self.db["checkpoints"].update_one(upsert_query, {"$set": doc}, upsert=True)
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Store intermediate writes linked to a checkpoint.

        This method saves intermediate writes associated with a checkpoint to the MongoDB database.

        Args:
            config (RunnableConfig): Configuration of the related checkpoint.
            writes (Sequence[Tuple[str, Any]]): List of writes to store, each as (channel, value) pair.
            task_id (str): Identifier for the task creating the writes.
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = config["configurable"]["checkpoint_id"]
        operations = []
        timestamp = datetime.now()
        
        for idx, (channel, value) in enumerate(writes):
            upsert_query = {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "idx": idx,
            }
            type_, serialized_value = self.serde.dumps_typed(value)
            operations.append(
                UpdateOne(
                    upsert_query,
                    {
                        "$set": {
                            "channel": channel,
                            "type": type_,
                            "value": serialized_value,
                            "timestamp": timestamp,
                        }
                    },
                    upsert=True,
                )
            )
        self.db["checkpoint_writes"].bulk_write(operations)

    def delete(self, thread_id=None, time_before=None, delete_all=False):
        """
        Deletes chat history from the MongoDB collection.

        Parameters:
        - thread_id (str, optional): The user_id whose chat history should be deleted.
        - time_before (datetime, optional): Deletes chat history before this datetime.
        - delete_all (bool, optional): If True, deletes all chat history for the user.

        Returns:
        - UpdateMany: The result of the update operation.
        """
        
        query = {}

        # If filtering by user and time_before
        if thread_id:
            query['thread_id'] = thread_id
        if time_before:
            query['timestamp'] = {'$lt': time_before}

        # If deleting all chat history for a specific user or all users
        if delete_all:
            # Remove entire chat history field
            print("database delete all")
            return [
                self.db["checkpoints"].delete_many({}),
                self.db["checkpoint_writes"].delete_many({}),
            ]
            
        print("database delete thread_id=", thread_id, ", before = ", time_before)
        return [
            self.db["checkpoints"].delete_many(query),
            self.db["checkpoint_writes"].delete_many(query),
        ]


if __name__=="__main__":
    # delete old chat history
    checkpointer = MongoDBSaver()
    checkpointer.delete(thread_id="test", time_before=timedelta(hours=6))
    checkpointer.delete(time_before=timedelta(days=7))