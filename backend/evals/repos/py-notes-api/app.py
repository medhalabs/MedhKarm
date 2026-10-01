"""A small notes API."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class NoteIn(BaseModel):
    title: str
    body: str = ""


class Note(NoteIn):
    id: int


def create_app() -> FastAPI:
    app = FastAPI(title="Notes")
    notes: dict[int, Note] = {}
    counter = {"next": 1}

    @app.post("/notes", status_code=201, response_model=Note)
    def create_note(note: NoteIn) -> Note:
        created = Note(id=counter["next"], **note.model_dump())
        notes[created.id] = created
        counter["next"] += 1
        return created

    @app.get("/notes", response_model=list[Note])
    def list_notes() -> list[Note]:
        return [notes[key] for key in sorted(notes)]

    @app.get("/notes/{note_id}", response_model=Note)
    def get_note(note_id: int) -> Note:
        if note_id not in notes:
            raise HTTPException(status_code=404, detail="Note not found")
        return notes[note_id]

    @app.delete("/notes/{note_id}", status_code=204)
    def delete_note(note_id: int) -> None:
        if note_id not in notes:
            raise HTTPException(status_code=404, detail="Note not found")
        del notes[note_id]

    return app


app = create_app()
