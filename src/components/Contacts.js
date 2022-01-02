import Contact from './Contact'

const Contacts = ({ contacts, onHover }) => {
    return (
        <div className='section'>
            <header className='header'>
                Contacting Me
            </header>

            {contacts.map((contact) => (
                <Contact
                    key={contact.id} 
                    contact={contact}
                    onHover={onHover}
                />
            ))}
        </div>
    )
}

export default Contacts
