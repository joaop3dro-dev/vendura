export default async function ProductById({params}) {
    const {id} = await params

    return (
        <h1>Produto {id}</h1>
    )
}
