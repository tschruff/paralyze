from paralyze.core.body.collision.contact import Penetrating


def detect(block, bodies_id, contact_type=Penetrating):
    bodies = block[bodies_id]
    contacts = []
    for b0 in bodies.iter_locals():
        for b1 in bodies.iter_bodies():
            contact = contact_type(b0, b1)
            if contact:
                contacts.append(contact)
    return contacts
